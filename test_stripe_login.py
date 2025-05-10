import os
from dotenv import load_dotenv
from stripe_automation import StripeHandler

def test_stripe_login():
    # Load environment variables
    load_dotenv()
    
    # Initialize StripeHandler with credentials and anti-captcha key
    handler = StripeHandler(
        email=os.getenv('EMAIL_ADDRESS'),
        password=os.getenv('STRIPE_PASSWORD'),
        anticaptcha_key=os.getenv('ANTICAPTCHA_KEY')
    )
    
    # Try logging in
    try:
        handler.sync_and_download_invoices()
        print("Successfully logged in to Stripe!")
    except Exception as e:
        print(f"Error during login: {str(e)}")

if __name__ == "__main__":
    test_stripe_login()
