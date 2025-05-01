# Zendesk Integration

## Overview
The Zendesk integration enables automatic retrieval of subscription and billing information from your Zendesk account. It supports both Zendesk Support and other Zendesk products.

## Setup

1. Create Zendesk API Token:
   - Log in to your Zendesk Admin Center
   - Go to Admin → Channels → API
   - Click "Add API Token"
   - Name your token and copy it
   - Note your Zendesk subdomain

2. Configure in Application:
   - Go to Settings
   - Navigate to Zendesk Integration
   - Enter your:
     - Subdomain
     - Email address
     - API Token
   - Save settings

## Features

- Subscription plan details
- Usage-based billing data
- Add-on purchases
- Historical invoice retrieval
- Automated report generation

## Technical Details

### Required Environment Variables
```env
ZENDESK_SUBDOMAIN=your_subdomain
ZENDESK_EMAIL=your_email
ZENDESK_API_TOKEN=your_api_token
```

### API Endpoints Used
```
- /api/v2/organization_subscriptions
- /api/v2/usage_records
- /api/v2/billing/invoices
- /api/v2/billing/subscription
```

### Security
- Token-based authentication
- Encrypted credential storage
- IP allowlisting support
- Rate limit compliance

## Troubleshooting

1. Authentication Issues:
   - Verify API token
   - Check email address
   - Confirm subdomain

2. Data Access Problems:
   - Verify admin privileges
   - Check subscription status
   - Review API access settings
