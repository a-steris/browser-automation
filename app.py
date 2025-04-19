from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response, send_file
import io
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import stripe
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from utils import generate_report_csv, send_slack_message
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))  # For session management
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load environment variables
load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        stripe_key = request.form.get('stripe_key')
        try:
            # Verify the key works by making a test API call
            stripe.Balance.retrieve(api_key=stripe_key)
            # If successful, create a session for the user
            user = User(stripe_key)
            login_user(user)
            session['stripe_key'] = stripe_key
            print("Login successful, redirecting to dashboard...")
            return redirect(url_for('dashboard'))
        except stripe.error.StripeError as e:
            print(f"Login error: {str(e)}")
            return render_template('login.html', error=str(e))
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    session.pop('stripe_key', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if 'stripe_key' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/balance')
@login_required
def get_balance():
    try:
        balance = stripe.Balance.retrieve(api_key=session['stripe_key'])
        return jsonify({
            'success': True,
            'balance': balance.available
        })
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/recent-payments')
@login_required
def get_recent_payments():
    try:
        limit = int(request.args.get('limit', 10))
        charges = stripe.Charge.list(
            limit=limit,
            api_key=session['stripe_key']
        )
        return jsonify({
            'success': True,
            'payments': [{
                'amount': charge.amount / 100,
                'currency': charge.currency,
                'status': charge.status,
                'description': charge.description,
                'created': datetime.fromtimestamp(charge.created).isoformat()
            } for charge in charges.data]
        })
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/recent-customers')
@login_required
def get_recent_customers():
    try:
        limit = int(request.args.get('limit', 10))
        customers = stripe.Customer.list(
            limit=limit,
            api_key=session['stripe_key']
        )
        return jsonify({
            'success': True,
            'customers': [{
                'email': customer.email,
                'created': datetime.fromtimestamp(customer.created).isoformat()
            } for customer in customers.data]
        })
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/create-test-data', methods=['POST'])
@login_required
def create_test_data():
    try:
        # Create test charges directly
        payments = []
        for i in range(3):
            charge = stripe.Charge.create(
                amount=1000,  # $10.00
                currency='usd',
                source='tok_visa',  # Test Visa card token
                description=f'Test payment {i+1}',
                api_key=session['stripe_key']
            )
            payments.append(charge)

        # Create test customers
        customers = []
        for i in range(3):
            customer = stripe.Customer.create(
                email=f'test{i}@example.com',
                description=f'Test customer {i+1}',
                source='tok_visa',  # Test Visa card token
                api_key=session['stripe_key']
            )
            customers.append(customer)

        return jsonify({
            'success': True,
            'message': 'Test data created successfully',
            'data': {
                'customers': len(customers),
                'payments': len(payments)
            }
        })
    except stripe.error.StripeError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/export/csv', methods=['GET', 'POST'])
@login_required
def export_csv():
    try:
        # Handle both GET and POST requests
        if request.method == 'POST':
            data = request.json
        else:
            data = request.args

        export_type = data.get('type', 'payments')
        notification_type = data.get('notification', 'download')  # download, email, or slack
        email = data.get('email')
        date_range = int(data.get('date_range', 30))  # Default to last 30 days
        
        if export_type == 'payments':
            # Get payment data with customer details
            charges = stripe.Charge.list(
                limit=100,
                created={'gte': int((datetime.now() - timedelta(days=date_range)).timestamp())},
                expand=['data.customer'],
                api_key=session['stripe_key']
            )
            
            payments = [{
                'amount': charge.amount / 100,
                'currency': charge.currency,
                'status': charge.status,
                'description': charge.description,
                'created': datetime.fromtimestamp(charge.created).isoformat(),
                'customer_email': charge.customer.email if charge.customer else None
            } for charge in charges.data]
            
            data = payments
            
        elif export_type == 'customers':
            # Get customer data with their payment history
            customers = stripe.Customer.list(
                limit=100,
                expand=['data.subscriptions'],
                api_key=session['stripe_key']
            )
            
            customer_data = []
            for customer in customers.data:
                # Get customer's charges
                charges = stripe.Charge.list(
                    customer=customer.id,
                    limit=100,
                    api_key=session['stripe_key']
                )
                
                total_spent = sum(charge.amount / 100 for charge in charges.data)
                
                customer_data.append({
                    'email': customer.email,
                    'created': datetime.fromtimestamp(customer.created).isoformat(),
                    'total_payments': len(charges.data),
                    'total_spent': total_spent
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
            success = send_slack_message(csv_content, export_type, data)
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# Vercel requires this
app.debug = False
