# Notion Integration

## Overview
The Notion integration enables automatic fetching and processing of invoices stored in Notion databases. It uses Notion's official API to securely access and retrieve invoice data.

## Setup

1. Create a Notion Integration:
   - Go to [Notion Developers](https://www.notion.so/my-integrations)
   - Click "New integration"
   - Name your integration
   - Select the workspace where your invoices are stored
   - Copy the "Internal Integration Token"

2. Configure Database Access:
   - Open your Notion invoice database
   - Click "Share" in the top right
   - Invite your integration
   - Copy the database ID from the URL

3. Configure in Application:
   - Go to Settings
   - Navigate to Notion Integration
   - Enter your Integration Token
   - Specify the Database ID
   - Save settings

## Features

- Automatic invoice detection and processing
- Support for multiple database formats
- Real-time sync with Notion
- Custom field mapping
- Bulk export capabilities

## Technical Details

### Required Environment Variables
```env
NOTION_API_KEY=your_integration_token
NOTION_DATABASE_ID=your_database_id
```

### Database Schema
Supported fields:
```
- Invoice Number
- Date
- Amount
- Currency
- Vendor/Company
- Status
- Category
- Notes
```

### Security
- API tokens are encrypted at rest
- Read-only access by default
- Automatic token refresh
- Rate limiting compliance

## Troubleshooting

1. Connection Issues:
   - Verify API token is valid
   - Check database permissions
   - Ensure database ID is correct

2. Data Sync Problems:
   - Verify database schema
   - Check field mappings
   - Review API rate limits
