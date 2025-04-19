import os
import stripe
from datetime import datetime
from dotenv import load_dotenv

class StripeReportDownloader:
    def __init__(self):
        print("Initializing Stripe Report Downloader...")
        
        # Load environment variables
        load_dotenv()
        self.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        if not self.api_key:
            raise Exception("Please set STRIPE_SECRET_KEY in .env file")
            
        # Initialize Stripe client
        stripe.api_key = self.api_key
        print("Stripe API client initialized successfully")
    
    def get_balance(self):
        """Get current balance"""
        try:
            balance = stripe.Balance.retrieve()
            print("\nCurrent Balance:")
            for balance_item in balance.available:
                print(f"{balance_item.currency.upper()}: {balance_item.amount/100:.2f}")
        except stripe.error.StripeError as e:
            print(f"Error retrieving balance: {str(e)}")
    
    def get_recent_payments(self, limit=10):
        """Get recent payments"""
        try:
            print(f"\nFetching last {limit} payments...")
            payments = stripe.PaymentIntent.list(limit=limit)
            for payment in payments.data:
                amount = payment.amount / 100  # Convert from cents to dollars
                status = payment.status
                created = datetime.fromtimestamp(payment.created)
                print(f"Amount: ${amount:.2f} | Status: {status} | Date: {created}")
        except stripe.error.StripeError as e:
            print(f"Error retrieving payments: {str(e)}")
    
    def get_recent_customers(self, limit=10):
        """Get recent customers"""
        try:
            print(f"\nFetching last {limit} customers...")
            customers = stripe.Customer.list(limit=limit)
            for customer in customers.data:
                email = customer.email or 'No email'
                created = datetime.fromtimestamp(customer.created)
                print(f"Customer: {email} | Created: {created}")
        except stripe.error.StripeError as e:
            print(f"Error retrieving customers: {str(e)}")

def main():
    try:
        downloader = StripeReportDownloader()
        
        # Get current balance
        downloader.get_balance()
        
        # Get recent payments
        downloader.get_recent_payments(5)
        
        # Get recent customers
        downloader.get_recent_customers(5)
        
    except Exception as e:
        print(f"Error: {str(e)}")
if __name__ == "__main__":
    main()