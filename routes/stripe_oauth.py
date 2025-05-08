from flask import Blueprint, redirect, request, url_for, session, jsonify
import stripe
import os
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

stripe_oauth_bp = Blueprint('stripe_oauth', __name__)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@stripe_oauth_bp.route('/oauth/stripe/connect', methods=['GET'])
def stripe_connect():
    """Redirect users to Stripe's OAuth authorization page"""
    client_id = os.getenv('STRIPE_CLIENT_ID')
    # Use ngrok HTTPS URL for the redirect URI
    redirect_uri = 'https://ed3f-2401-4900-1c3e-20ed-d447-4e3c-47f4-1359.ngrok-free.app/oauth/stripe/callback/'
    
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': 'read_write',
        'stripe_user[email]': 'your.email@example.com',  # Pre-fill email if you want
        'stripe_user[country]': 'US',  # Pre-set country to US
        'stripe_user[business_type]': 'company',
        'redirect_uri': redirect_uri
    }
    
    # Construct the OAuth URL
    oauth_url = 'https://connect.stripe.com/oauth/authorize?' + '&'.join([f'{key}={params[key]}' for key in params])
    return redirect(oauth_url)

@stripe_oauth_bp.route('/oauth/stripe/callback', methods=['GET'])
def oauth_callback():
    """Handle the OAuth callback from Stripe"""
    if 'error' in request.args:
        return jsonify({'error': request.args['error']}), 400
    
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No authorization code received'}), 400

    try:
        # Exchange the authorization code for an access token
        response = stripe.OAuth.token(
            grant_type='authorization_code',
            code=code,
        )
        
        # Store the access token and connected account ID
        connected_account_id = response['stripe_user_id']
        access_token = response['access_token']
        
        # Here you would typically store these in your database
        # For now, we'll store in session (not recommended for production)
        session['stripe_account_id'] = connected_account_id
        session['stripe_access_token'] = access_token
        
        return jsonify({
            'success': True,
            'message': 'Successfully connected to Stripe',
            'account_id': connected_account_id
        })
        
    except stripe.error.OAuth.OAuthError as e:
        return jsonify({'error': 'OAuth error: ' + str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Unexpected error: ' + str(e)}), 500
