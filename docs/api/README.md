# API Documentation

## Overview
The Browser Automation API provides endpoints for managing integrations, retrieving data, and generating reports. All endpoints require authentication and use HTTPS.

## Authentication

Session-based authentication is used for all API endpoints. Users must be logged in through the web interface.

## Endpoints

### AWS Integration

#### GET /auth/aws
Initiates the AWS OAuth flow.

#### GET /auth/aws/callback
Handles the AWS OAuth callback.

#### GET /disconnect/aws
Disconnects the AWS integration.

### Stripe Integration

#### POST /connect/stripe
```json
{
  "api_key": "sk_test_..."
}
```
Connects a Stripe account using an API key.

#### GET /disconnect/stripe
Disconnects the Stripe integration.

#### GET /api/stripe/report
Generates a CSV report of Stripe invoices.

### Slack Integration

#### POST /settings/slack
```json
{
  "webhook_url": "https://hooks.slack.com/..."
}
```
Configures Slack notifications.

## Response Format

All API responses follow this format:
```json
{
  "success": true|false,
  "data": {
    // Response data if successful
  },
  "error": "Error message if failed"
}
```

## Error Codes

- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

## Rate Limiting

- 100 requests per minute per IP
- 1000 requests per hour per user
- Stripe/AWS API limits are respected

## Security

- All requests must use HTTPS
- CSRF protection is enabled
- Session cookies are secure and HTTP-only
- API keys and tokens are encrypted at rest
