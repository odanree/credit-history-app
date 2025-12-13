"""
Flask Dashboard for Credit History Visualization
Displays Plaid transaction data in a web interface
"""
from flask import Flask, render_template, jsonify
import json
import os
import sys
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.plaid_integration import PlaidClient

load_dotenv()

app = Flask(__name__)

def get_credit_data():
    """Fetch fresh credit data from Plaid"""
    try:
        client_id = os.getenv('PLAID_CLIENT_ID')
        secret = os.getenv('PLAID_SECRET')
        env = os.getenv('PLAID_ENV', 'sandbox')
        access_token = os.getenv('PLAID_ACCESS_TOKEN')
        
        # Check for required environment variables
        if not client_id or not secret:
            print("Error: PLAID_CLIENT_ID or PLAID_SECRET not set in environment")
            return None
        
        if not access_token:
            print("Error: PLAID_ACCESS_TOKEN not found in .env")
            print("To generate an access token:")
            print("1. Run: python scripts/setup_plaid_token.py")
            print("2. Or manually complete Plaid Link flow")
            return None
        
        client = PlaidClient(client_id, secret, env)
        credit_data = client.get_credit_card_data(access_token)
        
        # Check if we got data back
        if not credit_data or 'error' in credit_data:
            error_msg = credit_data.get('error', 'Unknown error') if credit_data else 'No data returned'
            print(f"Error from Plaid API: {error_msg}")
            return None
            
        return credit_data
    except Exception as e:
        print(f"Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_transactions(transactions):
    """Analyze transactions for dashboard insights"""
    if not transactions:
        return {}
    
    # Group by month
    monthly_spending = defaultdict(float)
    # Group by category
    category_spending = defaultdict(float)
    # Top merchants
    merchant_spending = defaultdict(float)
    
    for txn in transactions:
        # Monthly totals
        date = txn.get('date', '')
        if date:
            # Convert date to string if it's a datetime object
            if isinstance(date, datetime):
                date_str = date.strftime('%Y-%m-%d')
            elif hasattr(date, 'isoformat'):
                date_str = date.isoformat()
            else:
                date_str = str(date)
            
            month = date_str[:7]  # YYYY-MM
            monthly_spending[month] += abs(txn.get('amount', 0))
        
        # Category totals
        category = txn.get('category')
        if category and isinstance(category, list):
            category_spending[category[0]] += abs(txn.get('amount', 0))
        else:
            category_spending['Other'] += abs(txn.get('amount', 0))
        
        # Merchant totals
        merchant = txn.get('name', 'Unknown')
        merchant_spending[merchant] += abs(txn.get('amount', 0))
    
    # Sort and get top items
    top_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:5]
    top_merchants = sorted(merchant_spending.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'monthly_spending': dict(sorted(monthly_spending.items())),
        'top_categories': top_categories,
        'top_merchants': top_merchants,
        'total_spent': sum(merchant_spending.values())
    }

@app.route('/')
def dashboard():
    """Main dashboard page"""
    credit_data = get_credit_data()
    
    if not credit_data:
        # Return setup instructions instead of error
        return render_template('setup.html', 
                             message="No Plaid access token configured. Please complete the setup steps."), 200
    
    analysis = analyze_transactions(credit_data.get('transactions', []))
    
    return render_template('dashboard.html', 
                         credit_data=credit_data,
                         analysis=analysis)

@app.route('/api/data')
def api_data():
    """API endpoint for credit data"""
    credit_data = get_credit_data()
    if credit_data:
        return jsonify(credit_data)
    return jsonify({'error': 'Failed to fetch data', 'message': 'PLAID_ACCESS_TOKEN not configured'}), 503

@app.route('/api/transactions')
def api_transactions():
    """API endpoint for transactions only"""
    credit_data = get_credit_data()
    if credit_data:
        return jsonify(credit_data.get('transactions', []))
    return jsonify({'error': 'Failed to fetch data', 'message': 'PLAID_ACCESS_TOKEN not configured'}), 503

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200

@app.route('/config-status')
def config_status():
    """Check configuration status"""
    return jsonify({
        'has_plaid_client_id': bool(os.getenv('PLAID_CLIENT_ID')),
        'has_plaid_secret': bool(os.getenv('PLAID_SECRET')),
        'has_plaid_access_token': bool(os.getenv('PLAID_ACCESS_TOKEN')),
        'plaid_env': os.getenv('PLAID_ENV', 'sandbox'),
        'needs_setup': not bool(os.getenv('PLAID_ACCESS_TOKEN'))
    }), 200

if __name__ == '__main__':
    # Local development
    print("\n🚀 Starting Credit History Dashboard...")
    print("📊 Open your browser to: http://localhost:5001")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, port=5001)
else:
    # Production (Render/Gunicorn)
    # Set Flask to production mode
    app.config['DEBUG'] = False
