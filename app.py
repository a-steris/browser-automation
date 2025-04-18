from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import stripe
from dotenv import load_dotenv
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
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
        payments = stripe.PaymentIntent.list(
            limit=limit,
            api_key=session['stripe_key']
        )
        return jsonify({
            'success': True,
            'payments': [{
                'amount': payment.amount / 100,
                'currency': payment.currency,
                'status': payment.status,
                'created': datetime.fromtimestamp(payment.created).isoformat()
            } for payment in payments.data]
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

if __name__ == '__main__':
    app.run()

# Vercel requires this
app.debug = False
