from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, session
from integrations.notion_client import NotionInvoiceClient
from utils.encryption import encrypt_data, decrypt_data

notion_bp = Blueprint('notion', __name__)

@notion_bp.route('/connect/notion', methods=['POST'])
def connect_notion():
    """Connect Notion integration with API key and database ID."""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        database_id = data.get('database_id')
        
        if not api_key or not database_id:
            return jsonify({
                'success': False,
                'error': 'API key and database ID are required'
            })
            
        # Test the connection
        client = NotionInvoiceClient(api_key, database_id)
        if not client.test_connection():
            return jsonify({
                'success': False,
                'error': 'Failed to connect to Notion. Please verify your credentials.'
            })
            
        # Store encrypted credentials in session
        session['notion_api_key'] = encrypt_data(api_key)
        session['notion_database_id'] = encrypt_data(database_id)
        
        return jsonify({
            'success': True,
            'message': 'Successfully connected to Notion'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error connecting to Notion: {str(e)}'
        })

@notion_bp.route('/disconnect/notion', methods=['POST'])
def disconnect_notion():
    """Disconnect Notion integration."""
    try:
        session.pop('notion_api_key', None)
        session.pop('notion_database_id', None)
        
        return jsonify({
            'success': True,
            'message': 'Successfully disconnected from Notion'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error disconnecting from Notion: {str(e)}'
        })

@notion_bp.route('/api/notion/invoices', methods=['GET'])
def get_notion_invoices():
    """Fetch invoices from Notion database."""
    try:
        if 'notion_api_key' not in session:
            return jsonify({
                'success': False,
                'error': 'Notion is not connected. Please connect your Notion account first.'
            })
            
        # Get query parameters
        days = request.args.get('days', default=365, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # Initialize client with decrypted credentials
        client = NotionInvoiceClient(
            api_key=decrypt_data(session['notion_api_key']),
            database_id=decrypt_data(session['notion_database_id'])
        )
        
        # Fetch invoices
        invoices = client.fetch_invoices(start_date=start_date)
        
        return jsonify({
            'success': True,
            'data': {
                'invoices': invoices
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error fetching Notion invoices: {str(e)}'
        })

@notion_bp.route('/api/notion/test', methods=['POST'])
def test_notion_connection():
    """Test Notion connection with provided credentials."""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        database_id = data.get('database_id')
        
        if not api_key or not database_id:
            return jsonify({
                'success': False,
                'error': 'API key and database ID are required'
            })
            
        client = NotionInvoiceClient(api_key, database_id)
        if client.test_connection():
            return jsonify({
                'success': True,
                'message': 'Successfully connected to Notion'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to Notion. Please verify your credentials.'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error testing Notion connection: {str(e)}'
        })
