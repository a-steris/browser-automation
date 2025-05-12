from app import app
import requests

def trigger_invoice_download():
    with app.test_client() as client:
        # First, visit settings to get a session
        client.get('/settings')
        
        # Save Stripe credentials
        response = client.post('/api/settings/stripe', json={
            'stripe_email': 'anyads.111@gmail.com',
            'stripe_password': 'Piano@2025'
        })
        print("Save credentials response:", response.json)
        
        # Trigger invoice download
        response = client.post('/api/invoices/sync-and-download')
        print("Download response:", response.data)

if __name__ == '__main__':
    trigger_invoice_download()
