# Browser Automation Documentation

This documentation provides comprehensive information about the Browser Automation project, which helps users automate their billing data collection from various platforms.

## Table of Contents

1. [Setup Guide](setup/README.md)
   - Installation
   - Environment Configuration
   - Running the Application

2. [Integrations](integrations/README.md)
   - [Stripe Integration](integrations/stripe.md)
   - [AWS Integration](integrations/aws.md)
   - [Slack Integration](integrations/slack.md)

3. [API Documentation](api/README.md)
   - Endpoints
   - Authentication
   - Response Formats

## Quick Start

1. Clone the repository
2. Set up environment variables in `.env`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python app.py`
5. Visit `http://localhost:5001` in your browser

## Security

- All sensitive credentials are encrypted at rest
- OAuth is used for secure authentication where available
- Read-only access is enforced for all integrations
