# AWS Integration

## Overview
The AWS integration allows users to connect their AWS account to view and analyze their AWS costs. It uses OAuth for secure authentication and only requests read-only access to billing data.

## Setup

1. Connect your AWS account by clicking the "Connect with AWS" button in either:
   - The main dashboard under the AWS section
   - The settings page under AWS Integration

2. You will be redirected to AWS to authorize the application
3. Grant read-only access to your billing data
4. You'll be redirected back to the application

## Features

- View AWS cost data in an easy-to-read format
- Download cost reports as CSV
- Automatic data refresh
- Secure credential storage

## Technical Details

### OAuth Configuration
Required environment variables:
```
AWS_CLIENT_ID=your_client_id
AWS_CLIENT_SECRET=your_client_secret
AWS_SSO_START_URL=your_sso_url
AWS_REDIRECT_URI=your_redirect_uri
AWS_REGION=your_aws_region
```

### IAM Policy
The application requires the following AWS managed policy:
- `AWSBillingReadOnlyAccess`

### Security
- Credentials are encrypted at rest
- Only read-only access is requested
- Token refresh is handled automatically
- Users can disconnect their AWS account at any time

## Troubleshooting

1. If connection fails:
   - Ensure all environment variables are set correctly
   - Check that the AWS SSO service is properly configured
   - Verify your AWS account has billing access enabled

2. If data isn't showing:
   - Verify the IAM role has the correct permissions
   - Check the AWS Cost Explorer API is enabled
   - Ensure your AWS account has billing data available
