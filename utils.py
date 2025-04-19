import csv
import io
from datetime import datetime

import os
import requests

def format_currency(amount, currency):
    return f"{amount:.2f} {currency.upper()}"

def generate_summary_stats(data, report_type):
    if report_type == 'payments':
        total_amount = sum(payment['amount'] for payment in data)
        successful = sum(1 for p in data if p['status'] == 'succeeded')
        failed = sum(1 for p in data if p['status'] != 'succeeded')
        return {
            'total_amount': total_amount,
            'total_count': len(data),
            'successful': successful,
            'failed': failed
        }
    elif report_type == 'customers':
        return {'total_customers': len(data)}
    return {}

def generate_report_csv(data, report_type='payments'):
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == 'payments':
        # Write header
        writer.writerow(['Amount', 'Currency', 'Status', 'Description', 'Date', 'Customer Email'])
        
        # Write data
        for payment in data:
            writer.writerow([
                f"{payment['amount']:.2f}",
                payment['currency'].upper(),
                payment['status'],
                payment.get('description', ''),
                datetime.fromisoformat(payment['created']).strftime('%Y-%m-%d %H:%M:%S'),
                payment.get('customer_email', '')
            ])
    elif report_type == 'customers':
        # Write header
        writer.writerow(['Email', 'Created Date', 'Total Payments', 'Total Spent'])
        
        # Write data
        for customer in data:
            writer.writerow([
                customer['email'],
                datetime.fromisoformat(customer['created']).strftime('%Y-%m-%d %H:%M:%S'),
                customer.get('total_payments', 0),
                format_currency(customer.get('total_spent', 0), 'usd')
            ])
    
    return output.getvalue()



def send_slack_message(csv_content, report_type='payments', data=None):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        raise ValueError("SLACK_WEBHOOK_URL not found in environment variables")
    
    try:
        # Generate summary statistics
        stats = generate_summary_stats(data, report_type)
        
        # Create formatted message
        filename = f"stripe_{report_type}_report_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # Format message based on report type
        if report_type == 'payments':
            message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "🏦 Stripe Payments Report"}
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Total Amount:*\n${stats['total_amount']:.2f}"},
                            {"type": "mrkdwn", "text": f"*Total Transactions:*\n{stats['total_count']}"},
                            {"type": "mrkdwn", "text": f"*Successful:*\n{stats['successful']}"},
                            {"type": "mrkdwn", "text": f"*Failed:*\n{stats['failed']}"}
                        ]
                    },
                    {
                        "type": "context",
                        "elements": [
                            {"type": "mrkdwn", "text": f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
                        ]
                    }
                ]
            }
        else:
            message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "👥 Stripe Customers Report"}
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Total Customers:*\n{stats['total_customers']}"}
                        ]
                    }
                ]
            }
        
        # Send message with the CSV content as text
        message['blocks'].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "```\n" + csv_content[:1000] + "\n```" # First 1000 chars of CSV
            }
        })
        
        response = requests.post(webhook_url, json=message)
        if response.status_code != 200:
            raise Exception(f"Failed to send message: {response.text}")
        
        return True
        
    except requests.RequestException as e:
        print(f"Network error sending Slack message: {str(e)}")
        return False
    except Exception as e:
        print(f"Error sending Slack message: {str(e)}")
        return False
