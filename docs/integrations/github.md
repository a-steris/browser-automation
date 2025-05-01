# GitHub Integration

## Overview
The GitHub integration allows automatic retrieval of subscription and billing information from GitHub's API. It supports both personal accounts and organizations.

## Setup

1. Create GitHub Access Token:
   - Go to [GitHub Settings > Developer settings](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - Select scopes:
     - `user`
     - `read:org` (for organization billing)
   - Copy the generated token

2. Configure in Application:
   - Go to Settings
   - Navigate to GitHub Integration
   - Enter your Access Token
   - Select organizations to monitor
   - Save settings

## Features

- Personal account billing history
- Organization subscription details
- Marketplace purchases tracking
- Usage-based billing data
- Automated report generation

## Technical Details

### Required Environment Variables
```env
GITHUB_ACCESS_TOKEN=your_access_token
GITHUB_APP_ID=your_app_id
GITHUB_APP_SECRET=your_app_secret
```

### API Endpoints Used
```
- /user/billing/history
- /orgs/{org}/billing/history
- /marketplace_listing/accounts
- /marketplace_listing/plans
```

### Security
- OAuth authentication
- Encrypted token storage
- Minimal scope requirements
- Rate limit handling

## Troubleshooting

1. Access Issues:
   - Verify token permissions
   - Check organization access
   - Review rate limits

2. Data Retrieval Problems:
   - Confirm billing access
   - Check organization membership
   - Verify marketplace subscriptions
