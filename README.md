# Asteris

A modern platform for managing and optimizing cloud costs across Stripe and AWS. Built with Flask and styled with Tailwind CSS.

## Features

- 📊 Real-time Stripe balance and transaction monitoring
- 📥 Export payment and customer reports as CSV
- 🔄 Multiple export options (Download, Email, Slack)
- 📱 Responsive design for desktop and mobile
- 🔒 Enterprise-grade security features
- 🧪 Test mode support for safe experimentation

## Security Features

- 🔐 End-to-end encryption for all sensitive data
- 🛡️ HTTPS/SSL encryption for all communications
- 🔒 Secure session management with HTTP-only cookies
- 🚫 Protection against XSS and CSRF attacks
- 🔑 Encrypted storage of API keys
- 📝 No persistent storage of sensitive data
- 🌐 Content Security Policy (CSP) implementation
- ⚡ Strict Transport Security (HSTS) enabled

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your configuration:
   ```bash
   cp .env.example .env
   ```

3. Generate secure keys for encryption and session management:
   ```bash
   # Generate a secure encryption key
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   
   # Generate a secure session key
   python -c "import os; print(os.urandom(24).hex())"
   ```

4. Configure your `.env` file with the generated keys:
   ```env
   # Required for encryption of sensitive data
   ENCRYPTION_KEY=your_generated_encryption_key
   
   # Required for secure session management
   SECRET_KEY=your_generated_session_key
   
   # Your API keys (these will be encrypted at rest)
   STRIPE_SECRET_KEY=your_stripe_key
   SLACK_WEBHOOK_URL=your_slack_webhook
   ```

3. Configure your environment variables in `.env`:
   ```
   SECRET_KEY=your_secret_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   SLACK_WEBHOOK_URL=your_slack_webhook_url  # Optional
   EMAIL_ADDRESS=your_email  # Optional
   EMAIL_PASSWORD=your_email_password  # Optional
   ```

## Usage

1. Start the server:
   ```bash
   python app.py
   ```

2. Visit `http://localhost:5001` in your browser

3. Log in using your Stripe Secret Key (test mode recommended)

4. Access features:
   - View real-time balance
   - Monitor recent payments
   - Generate and export reports
   - Send reports to Slack or email (for slack you have to connect a slack bot)

## Development

1. The application runs in test mode by default
2. Use Stripe test API keys for development
3. Test data can be generated from the dashboard
4. All API routes are protected with login_required

## Security Notes

1. Never commit your `.env` file to version control
2. Only use test mode API keys during development
3. Store production API keys securely
4. All sensitive routes require authentication
5. Data is transmitted securely via Stripe's API

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - feel free to use this project for your own purposes.