from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, send_file
from datetime import datetime, timedelta
from io import StringIO
from flask_cors import CORS

from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
from stripe_handler import StripeHandler
from decimal import Decimal
from dotenv import load_dotenv
from utils import generate_report_csv, send_slack_message
from functools import wraps
import os

app = Flask(__name__, static_url_path='/static', static_folder='static')

# Load environment variables
load_dotenv()

# Initialize encryption key
ENCRYPTION_KEY = b'zSl4qQJlxFET6_JvCeEpzDjQc-DINgEGTwu8Pnor1vw='
fernet = Fernet(ENCRYPTION_KEY)

# Configure Flask app
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')  # for session management

# Talisman configuration removed for local development
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Set secure cookie settings based on environment
is_production = os.getenv('FLASK_ENV') != 'development'
app.config['SESSION_COOKIE_SECURE'] = is_production  # Use secure cookies in production
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['SESSION_COOKIE_NAME'] = 'asteris_session'  # Custom session cookie name

# Configure Talisman security headers
# Security headers configuration for development
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True
)



# Encryption helpers
def encrypt_data(data):
    if not data:
        return None
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    if not encrypted_data:
        return None
    return fernet.decrypt(encrypted_data.encode()).decode()

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/settings/stripe', methods=['POST'])
def save_stripe_settings():
    app.logger.info("Received Stripe settings update request")
    data = request.get_json()
    
    stripe_email = data.get('stripe_email')
    stripe_password = data.get('stripe_password')
    
    if not all([stripe_email, stripe_password]):
        app.logger.error("Missing required Stripe credentials")
        return jsonify({
            'success': False,
            'error': 'Stripe login email and password are required'
        })
    
    try:
        # Save credentials in session
        app.logger.info("Saving credentials in session...")
        session['stripe_email'] = encrypt_data(stripe_email)
        session['stripe_password'] = encrypt_data(stripe_password)
        session.permanent = True
        
        app.logger.info("Stripe credentials saved successfully")
        return jsonify({'success': True})
        
    except Exception as e:
        app.logger.error(f"Error saving Stripe settings: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/settings/status')
def get_settings_status():
    stripe_connected = False
    slack_connected = False

    # Check Stripe connection
    app.logger.info("Checking Stripe connection...")
    stripe_email = session.get('stripe_email')
    stripe_password = session.get('stripe_password')
    
    # Consider connected if we have login credentials
    if all([stripe_email, stripe_password]):
        stripe_connected = True
        app.logger.info("Stripe connection successful")

    # Check if Slack webhook is configured
    slack_webhook = session.get('slack_webhook_url')
    slack_connected = bool(slack_webhook)

    return jsonify({
        'stripe_connected': stripe_connected,
        'slack_connected': slack_connected
    })

@app.route('/login')
def login():
    return redirect(url_for('settings'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('settings'))

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


@app.route('/dashboard')
def dashboard():
    app.logger.info(f"Dashboard: Session data = {dict(session)}")
    if not all([session.get('stripe_email'), session.get('stripe_password')]):
        app.logger.error("Missing Stripe credentials")
        return redirect('/settings')
    
    response = make_response(render_template('dashboard.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/balance')
def get_balance():
    app.logger.info('Fetching balance...')
    
    # Since we're not using the API, return mock data
    response = {
        'available': 0,
        'pending': 0,
        'instant_payouts': False
    }
    
    app.logger.info(f'Balance response: {response}')
    return jsonify(response)

@app.route('/api/recent-payments')
def get_recent_payments():
    app.logger.info('Fetching recent payments...')
    
    # Since we're not using the API, return mock data
    formatted_payments = []
    
    app.logger.info('No recent payments to show without Stripe API')
    
    return jsonify({
        'success': True,
        'payments': formatted_payments
    })

@app.route('/api/recent-customers')
def get_recent_customers():
    app.logger.info('Fetching recent customers...')
    
    # Since we're not using the API, return mock data
    formatted_customers = []
    
    app.logger.info('No recent customers to show without Stripe API')
    
    return jsonify({
        'success': True,
        'customers': formatted_customers
    })

@app.route('/api/create-test-data', methods=['POST'])
def create_test_data():
    try:
        # Decrypt the Stripe key
        stripe_key = decrypt_data(session['stripe_key'])
        stripe.api_key = stripe_key

        # Create test customers first
        customers = []
        for i in range(3):
            customer = stripe.Customer.create(
                email=f'test{i+1}@example.com',
                name=f'Test Customer {i+1}',
                description=f'Test customer {i+1}',
                source='tok_visa'  # Test Visa card token
            )
            customers.append(customer)

        # Create test charges for each customer
        payments = []
        amounts = [1000, 2000, 5000]  # $10, $20, $50
        for i, customer in enumerate(customers):
            charge = stripe.Charge.create(
                amount=amounts[i % len(amounts)],
                currency='usd',
                customer=customer.id,
                description=f'Test payment for {customer.email}'
            )
            payments.append(charge)

            # Create an invoice for each customer
            invoice_item = stripe.InvoiceItem.create(
                customer=customer.id,
                amount=amounts[i % len(amounts)],
                currency='usd',
                description=f'Test invoice item for {customer.email}'
            )
            
            invoice = stripe.Invoice.create(
                customer=customer.id,
                auto_advance=True,  # Auto-finalize the invoice
            )
            invoice.finalize_invoice()

        return jsonify({
            'success': True,
            'message': 'Test data created successfully',
            'data': {
                'customers': len(customers),
                'payments': len(payments)
            }
        })
    except stripe.error.StripeError as e:
        app.logger.error(f'Stripe error creating test data: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Stripe error: {str(e)}'
        })
    except Exception as e:
        app.logger.error(f'Unexpected error creating test data: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
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
def sync_and_download_invoices():
    """Download invoices using browser automation"""
    try:
        app.logger.info('Starting invoice download using browser automation...')
        
        # Get Stripe credentials from session
        stripe_email = decrypt_data(session.get('stripe_email', ''))
        stripe_password = decrypt_data(session.get('stripe_password', ''))
        
        if not stripe_email or not stripe_password:
            return jsonify({
                'success': False,
                'error': 'Stripe login credentials not found. Please configure them in settings.'
            })

        # Initialize the Stripe handler
        from stripe_handler import StripeHandler
        anticaptcha_key = os.getenv('ANTICAPTCHA_KEY')
        handler = StripeHandler(stripe_email, stripe_password)
        handler.anticaptcha_key = anticaptcha_key
        
        try:
            # Download invoices using browser automation
            app.logger.info('Starting browser automation...')
            download_path = handler.sync_and_download_invoices()
            
            if not download_path or not os.path.exists(download_path):
                raise Exception('Download failed - no file found')
                
            # Read the downloaded file
            with open(download_path, 'rb') as f:
                csv_data = f.read()
            
            # Create the response
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename=stripe_report_{datetime.now().strftime("%Y-%m-%d")}.csv'
            
            app.logger.info('Invoice download completed successfully')
            return response
            
        except Exception as e:
            app.logger.error(f'Browser automation error: {str(e)}')
            raise
            
    except Exception as e:
        app.logger.error(f'Error during invoice download: {str(e)}')
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



        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))  # Changed default port to 5001
    app.run(host='0.0.0.0', port=port, ssl_context=None, debug=True)

# Vercel requires this
app.debug = False
