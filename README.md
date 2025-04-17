# Stripe Report Downloader

A Python script that automates the process of logging into Stripe and downloading financial reports using Selenium WebDriver.

## Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file by copying `.env.example` and filling in your Stripe credentials:
   ```bash
   cp .env.example .env
   ```

3. Edit the `.env` file with your Stripe login credentials:
   ```
   STRIPE_EMAIL=your.email@example.com
   STRIPE_PASSWORD=your_stripe_password
   ```

## Usage

Run the script:
```bash
python stripe_report_downloader.py
```

The script will:
1. Launch a Chrome browser
2. Log into your Stripe account
3. Navigate to the Balance page
4. Download the payout report for the last 30 days
5. Save the report to the `downloads` directory

## Security Note

Never commit your `.env` file containing credentials to version control. The `.env` file is already included in `.gitignore`.