from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from datetime import datetime, timedelta
from io import StringIO
import io
import csv
import time
from flask import Flask, render_template, request, jsonify, session, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_talisman import Talisman
from flask_cors import CORS
from cryptography.fernet import Fernet
import stripe
import boto3
from botocore.exceptions import ClientError
import os
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
from utils import generate_report_csv, send_slack_message
from functools import wraps

app = Flask(__name__, static_url_path='/static', static_folder='static')

# Enable CORS
CORS(app, supports_credentials=True)

# Load environment variables
load_dotenv()

# Initialize encryption key
ENCRYPTION_KEY = b'zSl4qQJlxFET6_JvCeEpzDjQc-DINgEGTwu8Pnor1vw='
fernet = Fernet(ENCRYPTION_KEY)

# Configure Flask app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')  # for session management
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Set secure cookie settings based on environment
is_production = os.getenv('FLASK_ENV') != 'development'
app.config['SESSION_COOKIE_SECURE'] = is_production  # Use secure cookies in production
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['SESSION_COOKIE_NAME'] = 'asteris_session'  # Custom session cookie name

# Configure Talisman security headers
Talisman(app,
    force_https=False,  # Disable HTTPS enforcement
    strict_transport_security=False,
    session_cookie_secure=False,
    content_security_policy={
        'default-src': [
            "'self'",
            "'unsafe-inline'",
            "'unsafe-eval'",
            "http://localhost:5001",  # Allow localhost HTTP
            "https://cdn.tailwindcss.com",
            "https://unpkg.com",
            "https://cdn.jsdelivr.net",
            "https://api.stripe.com"
        ],
        'img-src': ["'self'", "data:", "https:"]
    }
)

# Initialize Flask-Login
# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Custom decorator for AWS configuration check
def aws_config_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not all(k in session for k in ['aws_access_key', 'aws_secret_key', 'aws_region']):
            return redirect(url_for('aws_config'))
        return f(*args, **kwargs)
    return decorated_function

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Encryption helpers
def encrypt_data(data):
    if not data:
        return None
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    if not encrypted_data:
        return None
    return fernet.decrypt(encrypted_data.encode()).decode()

class User(UserMixin):
    def __init__(self, user_id, stripe_account_id=None):
        self.id = user_id
        self.stripe_account_id = stripe_account_id

@login_manager.user_loader
def load_user(user_id):
    # In a real application, you would load the user from your database
    return User(user_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/settings/stripe', methods=['POST'])
def save_stripe_settings():
    app.logger.info(f"Session before: {dict(session)}")
    app.logger.info(f"Received form data: {dict(request.form)}")
    
    stripe_key = request.form.get('stripe_key')
    if not stripe_key:
        app.logger.error("No Stripe key provided")
        return redirect('/settings')
    
    app.logger.info(f"Stripe key length: {len(stripe_key)}")
    
    try:
        # First verify the key works
        app.logger.info("Verifying Stripe key...")
        stripe.api_key = stripe_key
        stripe.Balance.retrieve()
        app.logger.info("Stripe key verified successfully")
        
        # Then save it in session
        app.logger.info("Saving key in session...")
        encrypted_key = encrypt_data(stripe_key)
        session.clear()  # Clear any existing session data
        session['stripe_key'] = encrypted_key
        session.permanent = True  # Make the session permanent
        app.logger.info(f"Session after: {dict(session)}")
        
        app.logger.info("Redirecting to dashboard...")
        response = redirect('/dashboard')
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        if 'stripe_key' in session:
            del session['stripe_key']
            session.modified = True
        return redirect('/settings')

@app.route('/api/settings/aws', methods=['POST'])
def save_aws_settings():
    data = request.get_json()
    aws_access_key = data.get('aws_access_key')
    aws_secret_key = data.get('aws_secret_key')
    aws_region = data.get('aws_region')
    
    if not all([aws_access_key, aws_secret_key, aws_region]):
        return jsonify({'success': False, 'error': 'All AWS credentials are required'})
    
    # Verify AWS credentials before saving
    try:
        client = boto3.client(
            'ce',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        # Try a simple API call to verify credentials
        client.get_cost_and_usage(
            TimePeriod={
                'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'End': datetime.now().strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        session['aws_access_key'] = aws_access_key
        session['aws_secret_key'] = aws_secret_key
        session['aws_region'] = aws_region
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/settings/status')
def get_settings_status():
    stripe_connected = False
    aws_connected = False

    # Check Stripe connection
    print("Checking Stripe connection...")
    stripe_key = session.get('stripe_key')
    print(f"Stripe key in session: {'Yes' if stripe_key else 'No'}")
    
    if stripe_key:
        try:
            print(f"Encrypted key length: {len(stripe_key)}")
            decrypted_key = decrypt_data(stripe_key)
            print(f"Decrypted key starts with: {decrypted_key[:5]}...")
            stripe.api_key = decrypted_key
            stripe.Account.retrieve()
            stripe_connected = True
            print("Stripe connection successful")
        except Exception as e:
            print(f"Error checking Stripe connection: {str(e)}")
            session.pop('stripe_key', None)
    
    # Check AWS connection
    if all(session.get(k) for k in ['aws_access_key', 'aws_secret_key', 'aws_region']):
        try:
            client = boto3.client(
                'ce',
                aws_access_key_id=session['aws_access_key'],
                aws_secret_access_key=session['aws_secret_key'],
                region_name=session['aws_region']
            )
            client.get_cost_and_usage(
                TimePeriod={
                    'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'End': datetime.now().strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            aws_connected = True
        except:
            session.pop('aws_access_key', None)
            session.pop('aws_secret_key', None)
            session.pop('aws_region', None)
    
    return jsonify({
        'stripe_connected': stripe_connected,
        'aws_connected': aws_connected
    })

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            
            # Get the next URL from query parameters
            next_page = request.args.get('next')
            
            # If next_page is AWS config save, save the AWS credentials
            if next_page and 'aws/save' in next_page:
                data = request.get_json()
                if data:
                    session['aws_access_key'] = data.get('aws_access_key')
                    session['aws_secret_key'] = data.get('aws_secret_key')
                    session['aws_region'] = data.get('aws_region')
            
            # Always redirect to dashboard after login
            return redirect(url_for('dashboard'))
        
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    session.pop('stripe_key', None)
    return redirect(url_for('index'))

def sync_invoices_background(stripe_key):
    """Background task to sync invoices every 5 minutes"""
    try:
        while True:
            print("Starting invoice sync...")
            stripe.api_key = stripe_key
            
            # Get all invoices from the last 24 hours
            invoices = stripe.Invoice.list(
                limit=100,
                created={'gte': int(time.time() - 86400)}  # Last 24 hours
            )
            
            # Store in session for quick access
            session['latest_invoices'] = [{
                'id': inv.id,
                'amount': inv.amount_due / 100,  # Convert from cents
                'status': inv.status,
                'customer': inv.customer,
                'created': inv.created
            } for inv in invoices.data]
            
            print(f"Synced {len(invoices.data)} invoices")
            time.sleep(300)  # Wait 5 minutes
    except Exception as e:
        print(f"Invoice sync error: {str(e)}")

def require_stripe_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'stripe_key' not in session:
            print("No stripe_key in session, redirecting to settings")
            return redirect('/settings')
        try:
            stripe.api_key = decrypt_data(session['stripe_key'])
            print("Set stripe.api_key successfully")
            return f(*args, **kwargs)
        except Exception as e:
            print("Error in require_stripe_key:", str(e))
            return redirect('/settings')
    return decorated_function

@app.route('/dashboard')
def dashboard():
    app.logger.info(f"Dashboard: Session data = {dict(session)}")
    if 'stripe_key' not in session:
        app.logger.error("No stripe_key in session for dashboard")
        return redirect('/settings')
    
    try:
        stripe_key = decrypt_data(session['stripe_key'])
        stripe.api_key = stripe_key
        app.logger.info("Set stripe.api_key for dashboard")
        
        # Verify the key still works
        stripe.Balance.retrieve()
        app.logger.info("Stripe key verified in dashboard")
        
        response = make_response(render_template('dashboard.html'))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    except Exception as e:
        app.logger.error(f"Error in dashboard: {str(e)}")
        if 'stripe_key' in session:
            del session['stripe_key']
            session.permanent = True
        return redirect('/settings')

@app.route('/api/balance')
def get_balance():
    app.logger.info('Fetching balance...')
    if 'stripe_key' not in session:
        app.logger.error('No Stripe key in session for balance')
        return jsonify({'error': 'No Stripe key in session'}), 401
    
    try:
        stripe_key = decrypt_data(session['stripe_key'])
        stripe.api_key = stripe_key
        balance = stripe.Balance.retrieve()
        app.logger.info(f'Balance fetched successfully: {balance}')
        return jsonify(balance)
    except Exception as e:
        app.logger.error(f'Error getting balance: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-payments')
def get_recent_payments():
    app.logger.info('Fetching recent payments...')
    if 'stripe_key' not in session:
        app.logger.error('No Stripe key in session for payments')
        return jsonify({'error': 'No Stripe key in session'}), 401
    
    try:
        stripe_key = decrypt_data(session['stripe_key'])
        stripe.api_key = stripe_key
        limit = request.args.get('limit', default=5, type=int)
        charges = stripe.Charge.list(limit=limit)
        
        payments = [{
            'amount': charge.amount / 100,
            'currency': charge.currency,
            'description': charge.description or 'Payment',
            'created': charge.created * 1000,  # Convert to milliseconds for JS
            'status': charge.status
        } for charge in charges.data]
        
        app.logger.info(f'Fetched {len(payments)} recent payments')
        return jsonify({
            'success': True,
            'payments': payments
        })
    except Exception as e:
        app.logger.error(f'Error getting payments: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-customers')
def get_recent_customers():
    app.logger.info('Fetching recent customers...')
    if 'stripe_key' not in session:
        app.logger.error('No Stripe key in session for customers')
        return jsonify({'error': 'No Stripe key in session'}), 401
    
    try:
        stripe_key = decrypt_data(session['stripe_key'])
        stripe.api_key = stripe_key
        limit = request.args.get('limit', default=5, type=int)
        customers = stripe.Customer.list(limit=limit)
        app.logger.info(f'Fetched {len(customers.data)} customers')
        
        customer_data = [{
            'email': customer.email,
            'created': customer.created * 1000,  # Convert to milliseconds for JS
            'delinquent': customer.delinquent
        } for customer in customers.data]
        
        return jsonify({
            'success': True,
            'customers': customer_data
        })
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/create-test-data', methods=['POST'])
def create_test_data():
    try:
        print('Starting test data creation...')
        if 'stripe_key' not in session:
            print('No Stripe key in session')
            return jsonify({'success': False, 'error': 'Stripe key not found'})
            
        # Decrypt the Stripe key
        try:
            stripe_key = decrypt_data(session['stripe_key'])
            stripe.api_key = stripe_key
            print('Successfully set Stripe key')
        except Exception as e:
            print(f'Error decrypting Stripe key: {str(e)}')
            return jsonify({'success': False, 'error': f'Error decrypting Stripe key: {str(e)}'})
            
        # Create test customers first
        print('Creating test customers...')
        customers = []
        for i in range(3):
            try:
                customer = stripe.Customer.create(
                    email=f'test{i}@example.com',
                    description=f'Test customer {i+1}',
                    source='tok_visa'  # Test Visa card token
                )
                customers.append(customer)
                print(f'Created customer {i+1}')
            except Exception as e:
                print(f'Error creating customer {i+1}: {str(e)}')
                return jsonify({'success': False, 'error': f'Error creating customer: {str(e)}'})

        # Create test products and prices
        print('Creating test product and price...')
        try:
            product = stripe.Product.create(
                name='Test Product',
                description='Product for testing'
            )
            print('Created product')
            
            price = stripe.Price.create(
                product=product.id,
                unit_amount=1000,  # $10.00
                currency='usd'
            )
            print('Created price')
        except Exception as e:
            print(f'Error creating product/price: {str(e)}')
            return jsonify({'success': False, 'error': f'Error creating product/price: {str(e)}'})

        # Create invoices for each customer
        print('Creating invoices...')
        invoices = []
        for i, customer in enumerate(customers, 1):
            try:
                # Create invoice items
                print(f'Creating invoice items for customer {i}...')
                stripe.InvoiceItem.create(
                    customer=customer.id,
                    price=price.id,
                    quantity=1
                )
                
                # Create and finalize invoice
                print(f'Creating invoice for customer {i}...')
                invoice = stripe.Invoice.create(
                    customer=customer.id,
                    auto_advance=True,  # Auto-finalize the invoice
                    collection_method='charge_automatically'
                )
                
                # Pay the invoice
                print(f'Paying invoice for customer {i}...')
                invoice.pay()
                invoices.append(invoice)
                print(f'Successfully created and paid invoice for customer {i}')
            except Exception as e:
                print(f'Error creating invoice for customer {i}: {str(e)}')
                return jsonify({'success': False, 'error': f'Error creating invoice: {str(e)}'})

        return jsonify({
            'success': True,
            'message': 'Test data created successfully',
            'data': {
                'customers': len(customers),
                'invoices': len(invoices)
            }
        })
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/settings/slack', methods=['POST'])
def save_slack_settings():
    data = request.get_json()
    webhook_url = data.get('webhook_url')
    if not webhook_url:
        return jsonify({'success': False, 'error': 'Slack webhook URL is required'})
    
    # Save to session instead of environment variable
    session['slack_webhook_url'] = webhook_url
    return jsonify({'success': True})

@app.route('/api/invoices/sync-and-download', methods=['POST'])
@require_stripe_key
def sync_and_download_invoices():
    """Sync latest invoices and return as CSV"""
    try:
        print("Starting invoice sync...")
        print(f"Session keys: {session.keys()}")
        
        if 'stripe_key' not in session:
            return jsonify({
                'success': False,
                'error': 'Stripe key not found in session. Please set up your Stripe credentials first.'
            })
            
        # Decrypt Stripe key
        try:
            stripe_key = decrypt_data(session['stripe_key'])
            stripe.api_key = stripe_key
            print("Successfully decrypted and set Stripe key")
        except Exception as e:
            print(f"Error decrypting Stripe key: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Error decrypting Stripe key. Please try setting up your Stripe credentials again.'
            })

        # Get invoices from the last 365 days
        print('Fetching invoices from the last year...')
        one_year_ago = int((datetime.now() - timedelta(days=365)).timestamp())
        
        # Get all invoices using auto-pagination
        invoices = []
        try:
            print(f'Searching for invoices created after {datetime.fromtimestamp(one_year_ago)}...')
            for invoice in stripe.Invoice.list(
                created={'gte': one_year_ago},
                limit=100,
                expand=['data.customer']
            ).auto_paging_iter():
                invoices.append(invoice)
                # Limit to 1000 invoices for performance
                if len(invoices) >= 1000:
                    break
            print(f'Found {len(invoices)} invoices')
        except Exception as e:
            print(f'Error fetching invoices: {str(e)}')
            return jsonify({
                'success': False,
                'error': f'Error fetching invoices: {str(e)}'
            })

        # Convert to list of dicts
        invoice_data = []
        for inv in invoices:
            # Get customer details
            customer_email = 'N/A'
            if inv.customer:
                try:
                    customer = stripe.Customer.retrieve(inv.customer)
                    customer_email = customer.email or 'N/A'
                except stripe.error.StripeError:
                    pass

            invoice_data.append({
                'Invoice ID': inv.id,
                'Amount': f"${inv.amount_due / 100:.2f}",
                'Status': inv.status,
                'Customer Email': customer_email,
                'Created Date': datetime.fromtimestamp(inv.created).strftime('%Y-%m-%d %H:%M:%S'),
                'Due Date': datetime.fromtimestamp(inv.due_date).strftime('%Y-%m-%d %H:%M:%S') if inv.due_date else 'N/A',
                'Paid': 'Yes' if inv.paid else 'No',
                'Description': inv.description or 'N/A'
            })

        if not invoice_data:
            return jsonify({
                'success': False,
                'error': 'No invoices found in the last year'
            })

        # Create CSV in memory
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=invoice_data[0].keys())
        writer.writeheader()
        writer.writerows(invoice_data)

        # Create the response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=stripe_invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        return response

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def generate_report_csv(data, export_type):
    output = StringIO()
    writer = csv.writer(output)
    
    if export_type == 'payments':
        writer.writerow(['Amount', 'Currency', 'Status', 'Description', 'Created', 'Customer Email'])
        for payment in data:
            writer.writerow([
                payment['amount'],
                payment['currency'],
                payment['status'],
                payment['description'],
                payment['created'],
                payment['customer_email']
            ])
    elif export_type == 'customers':
        writer.writerow(['Email', 'Created', 'Total Payments', 'Total Spent'])
        for customer in data:
            writer.writerow([
                customer['email'],
                customer['created'],
                customer['total_payments'],
                customer['total_spent']
            ])
    
    return output.getvalue()

@app.route('/api/export/csv', methods=['GET', 'POST'])
@require_stripe_key
def export_csv():
    try:
        # Handle both GET and POST requests
        if request.method == 'POST':
            data = request.json
        else:
            data = request.args

        # Decrypt Stripe key
        stripe_key = decrypt_data(session['stripe_key'])
        stripe.api_key = stripe_key

        export_type = data.get('type', 'payments')
        notification_type = data.get('notification', 'download')  # download, email, or slack
        email = data.get('email')
        date_range = int(data.get('date_range', 30))  # Default to last 30 days
        
        if export_type == 'payments':
            # Get payment data with customer details
            charges = stripe.Charge.list(
                limit=100,
                created={'gte': int((datetime.now() - timedelta(days=date_range)).timestamp())}
            )
            
            payments = []
            for charge in charges.data:
                customer = None
                if charge.customer:
                    try:
                        customer = stripe.Customer.retrieve(charge.customer)
                    except stripe.error.StripeError:
                        pass

                payment_data = {
                    'amount': f"{charge.amount / 100:.2f}",
                    'currency': charge.currency.upper(),
                    'status': charge.status,
                    'description': charge.description or 'No description',
                    'created': datetime.fromtimestamp(charge.created).strftime('%Y-%m-%d %H:%M:%S'),
                    'customer_email': customer.email if customer else 'No customer'
                }
                payments.append(payment_data)
            
            data = payments
            
        elif export_type == 'customers':
            # Get customer data with their payment history
            customers = stripe.Customer.list(limit=100)
            
            customer_data = []
            for customer in customers.data:
                # Get customer's charges
                charges = stripe.Charge.list(
                    customer=customer.id,
                    limit=100
                )
                
                total_spent = sum(charge.amount / 100 for charge in charges.data)
                
                customer_data.append({
                    'email': customer.email or 'No email',
                    'created': datetime.fromtimestamp(customer.created).strftime('%Y-%m-%d %H:%M:%S'),
                    'total_payments': len(charges.data),
                    'total_spent': f"{total_spent:.2f}"
                })
            
            data = customer_data
        
        # Generate CSV
        csv_content = generate_report_csv(data, export_type)
        
        # Handle different notification types
        if notification_type == 'email' and email:
            send_email_report(email, csv_content, export_type)
            return jsonify({
                'success': True,
                'message': f'Report sent to {email}'
            })
        elif notification_type == 'slack':
            if 'slack_webhook_url' not in session:
                return jsonify({'success': False, 'error': 'Please configure Slack webhook URL in settings'})
            success = send_slack_message(csv_content, export_type, data, webhook_url=session['slack_webhook_url'])
            return jsonify({
                'success': success,
                'message': 'Report sent to Slack' if success else 'Failed to send to Slack'
            })
        elif notification_type == 'download':
            filename = f'stripe_{export_type}_report_{datetime.now().strftime("%Y%m%d")}.csv'
            return send_file(
                io.BytesIO(csv_content.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
                
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': f'Stripe API error: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# AWS Routes
@app.route('/aws/config')
def aws_config():
    return render_template('aws_config.html')

@app.route('/api/settings/aws/save', methods=['POST'])
def save_aws_credentials():
    if not request.is_json:
        return jsonify({
            'success': False,
            'error': 'Content-Type must be application/json'
        }), 400

    data = request.get_json()
    
    try:
        # Test AWS credentials using STS GetCallerIdentity
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=data['aws_access_key'],
            aws_secret_access_key=data['aws_secret_key'],
            region_name=data['aws_region']
        )
        
        # This API call will verify if credentials are valid
        response = sts_client.get_caller_identity()
        
        # If we get here, credentials are valid - save them
        session['aws_access_key'] = data['aws_access_key']
        session['aws_secret_key'] = data['aws_secret_key']
        session['aws_region'] = data['aws_region']
        
        return jsonify({
            'success': True,
            'message': 'AWS configuration saved successfully',
            'redirect': url_for('dashboard')
        })
    except KeyError as e:
        return jsonify({
            'success': False,
            'error': f'Missing required field: {str(e)}'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/aws/costs')
def get_aws_costs():
    try:
        if not all(k in session for k in ['aws_access_key', 'aws_secret_key']):
            return jsonify({
                'success': False,
                'error': 'AWS credentials not found'
            })

        # First verify AWS credentials are still valid
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=session['aws_access_key'],
            aws_secret_access_key=session['aws_secret_key'],
            region_name=session.get('aws_region', 'us-east-1')
        )
        sts_client.get_caller_identity()

        try:
            # Try to get cost data if we have permissions
            client = boto3.client(
                'ce',
                aws_access_key_id=session['aws_access_key'],
                aws_secret_access_key=session['aws_secret_key'],
                region_name=session.get('aws_region', 'us-east-1')
            )

            end = datetime.now()
            start = end - timedelta(days=60)  # Get 2 months of data

            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start.strftime('%Y-%m-%d'),
                    'End': end.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[{
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }]
            )

            # Calculate costs
            costs = {
                'current_month': 0.0,
                'previous_month': 0.0,
                'projected': 0.0,
                'by_service': []
            }

            # Process each time period
            for period in response['ResultsByTime']:
                total = sum(float(group['Metrics']['UnblendedCost']['Amount'])
                           for group in period['Groups'])
                
                # Add to service breakdown for current month
                if period == response['ResultsByTime'][-1]:
                    costs['current_month'] = total
                    costs['by_service'] = [
                        {
                            'service': group['Keys'][0],
                            'amount': float(group['Metrics']['UnblendedCost']['Amount'])
                        }
                        for group in period['Groups']
                    ]
                elif period == response['ResultsByTime'][-2]:
                    costs['previous_month'] = total

            # Calculate projected cost
            days_in_month = calendar.monthrange(end.year, end.month)[1]
            days_so_far = end.day
            if days_so_far > 0:
                costs['projected'] = costs['current_month'] * (days_in_month / days_so_far)

            # Sort services by cost
            costs['by_service'].sort(key=lambda x: x['amount'], reverse=True)

            return jsonify({
                'success': True,
                'costs': costs
            })

        except Exception as e:
            # Return a default response if we can't access cost data
            return jsonify({
                'success': True,
                'costs': {
                    'current_month': 0.0,
                    'previous_month': 0.0,
                    'projected': 0.0,
                    'by_service': [],
                    'warning': 'Cost Explorer access denied. Please ensure your AWS user has the required permissions.'
                }
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))  # Changed default port to 5001
    app.run(host='0.0.0.0', port=port)

# Vercel requires this
app.debug = False
