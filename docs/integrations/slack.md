# Slack Integration

## Overview
The Slack integration allows users to receive automated notifications and reports through their Slack workspace. It uses webhook URLs for simple setup and secure communication.

## Setup

1. Create a Slack Webhook:
   - Go to your Slack workspace
   - Create a new app or use an existing one
   - Enable Incoming Webhooks
   - Create a new webhook URL for a specific channel

2. Configure the Integration:
   - Go to Settings in the application
   - Navigate to the Slack Integration section
   - Enter your webhook URL
   - Save the settings

## Features

- Automated report delivery
- Customizable notification settings
- Secure webhook handling
- Channel-specific messaging

## Technical Details

### Webhook Configuration
Required settings:
```
SLACK_WEBHOOK_URL=your_webhook_url
```

### Security
- HTTPS-only communication
- Webhook URLs are encrypted at rest
- Rate limiting is enforced
- No sensitive data is sent to Slack

### Message Format
Notifications include:
- Report generation status
- Basic summary statistics
- Links to detailed reports

## Troubleshooting

1. If notifications aren't working:
   - Verify the webhook URL is valid
   - Check Slack app permissions
   - Ensure the channel still exists
   - Verify network connectivity

2. For message delivery issues:
   - Check rate limits
   - Verify message format
   - Ensure webhook hasn't been revoked
