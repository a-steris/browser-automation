import os
from datetime import datetime
from stripe_automation import StripeHandler as AutomationHandler

class StripeHandler:
    def __init__(self, email=None, password=None):
        self.email = email or os.getenv('STRIPE_EMAIL')
        self.password = password or os.getenv('STRIPE_PASSWORD')
        self.download_dir = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(self.download_dir, exist_ok=True)

    def sync_and_download_invoices(self):
        """
        Download invoices using browser automation
        Returns the path to the downloaded file
        """
        if not self.email or not self.password:
            raise ValueError("Stripe credentials not set")

        try:
            handler = AutomationHandler(self.email, self.password)
            download_path = handler.sync_and_download_invoices()
            return download_path
        except Exception as e:
            raise Exception(f"Failed to download invoices: {str(e)}")

    def get_latest_download(self):
        """Get the most recent downloaded file"""
        try:
            files = [f for f in os.listdir(self.download_dir) if f.endswith('.csv')]
            if not files:
                return None
            files.sort(key=lambda x: os.path.getmtime(os.path.join(self.download_dir, x)), reverse=True)
            return os.path.join(self.download_dir, files[0])
        except Exception:
            return None
