# Stripe Integration

## Overview
The Stripe integration enables users to securely connect their Stripe account to view and analyze their invoice data. It currently uses API key authentication with plans to support OAuth in the future.

## Setup

1. Get your Stripe API key:
   - Go to your Stripe Dashboard
   - Navigate to Developers → API keys
   - Create a new Restricted Key with read-only access to:
     - Invoices
     - Customers
     - Products

2. Connect your Stripe account:
   - Click "Connect with Stripe" in the dashboard
   - Enter your API key
   - The application will verify the key and establish the connection

## Features

- View all invoices from the last 365 days
- Download invoice data as CSV
- Real-time data synchronization
- Secure credential storage

## Technical Details

### Authentication
Currently uses API key authentication with the following security measures:
- Keys must be restricted with minimum required permissions
- Keys are encrypted at rest using AES-256
- Keys can be revoked at any time from the Stripe dashboard

### Required Permissions
The API key should have read-only access to:
```
- invoices:read
- customers:read
- products:read
```

### Environment Variables
```
ENCRYPTION_KEY=your_encryption_key
```

### Future Plans
- OAuth integration for simpler setup
- Enhanced security features
- More granular permission controls

## Troubleshooting

1. If connection fails:
   - Verify the API key is valid
   - Check that the key has the required permissions
   - Ensure the key hasn't been revoked

2. If data isn't showing:
   - Confirm your Stripe account has invoices
   - Check the date range of available data
   - Verify the API key permissions
