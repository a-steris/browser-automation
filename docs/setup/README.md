# Setup Guide

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Git (for version control)
- Access to AWS and Stripe accounts (for integrations)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/browser-automation.git
cd browser-automation
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

2. Configure the required environment variables:

```env
# Application
ENCRYPTION_KEY=your_encryption_key

# AWS Integration
AWS_CLIENT_ID=your_client_id
AWS_CLIENT_SECRET=your_client_secret
AWS_SSO_START_URL=your_sso_url
AWS_REDIRECT_URI=your_redirect_uri
AWS_REGION=your_aws_region

# Optional: Slack Integration
SLACK_WEBHOOK_URL=your_webhook_url
```

## Running the Application

1. Start the application:
```bash
python app.py
```

2. Access the web interface:
- Open `http://localhost:5001` in your browser
- Click "Connect with AWS" or "Connect with Stripe" to set up integrations
- Configure Slack notifications in Settings if desired

## Development Setup

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

3. Run tests:
```bash
pytest
```

## Security Considerations

1. Use strong encryption keys
2. Keep `.env` file secure and never commit it
3. Use minimum required permissions for API keys
4. Regularly rotate credentials
5. Monitor access logs

## Troubleshooting

1. Port conflicts:
   - Check if port 5001 is in use
   - Kill conflicting processes or change port

2. Environment issues:
   - Verify all required variables are set
   - Check variable format and values
   - Ensure encryption key is valid

3. Integration problems:
   - Verify API credentials
   - Check network connectivity
   - Review integration-specific docs
