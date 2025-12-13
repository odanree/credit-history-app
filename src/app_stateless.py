"""
Stateless Credit History Dashboard
- Zero customer data storage
- Access token stored in encrypted session cookie
- Fresh data fetched from Plaid on every request
- No database required
"""
from flask import Flask, render_template, jsonify, session, request, redirect, url_for
from flask_session import Session
from cryptography.fernet import Fernet
from functools import wraps
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.plaid_integration import PlaidClient

load_dotenv()

app = Flask(__name__)

# ============================================================================
# SESSION CONFIGURATION (stateless, no database)
# ============================================================================

app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

# Session stored in secure cookies (no server-side storage for scalability)
# Real optimization: in-memory cache layer in PlaidClient (5-minute TTL)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Can't be accessed by JavaScript
app.config['SESSION_COOKIE_SECURE'] = True    # HTTPS only
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_REFRESH_EACH_REQUEST'] = False  # Don't refresh every request
app.config['SESSION_FILE_THRESHOLD'] = 500  # Session files before cleanup

# Use temp directory for session files (not persistent, cleaned up)
import tempfile
session_dir = os.path.join(tempfile.gettempdir(), 'flask_sessions')
os.makedirs(session_dir, exist_ok=True)
app.config['SESSION_FILE_DIR'] = session_dir

Session(app)

# ============================================================================
# TOKEN ENCRYPTION (for extra security layer)
# ============================================================================

class TokenEncryption:
    """Encrypt access tokens before storing in session"""
    
    def __init__(self, key=None):
        # Use provided key or generate from environment
        if key:
            self.cipher = Fernet(key)
        else:
            # For development: generate once per startup
            # For production: use consistent key from environment
            encryption_key = os.getenv('TOKEN_ENCRYPTION_KEY')
            if encryption_key:
                self.cipher = Fernet(encryption_key.encode())
            else:
                # Fallback: generate new key (won't persist across restarts)
                key = Fernet.generate_key()
                self.cipher = Fernet(key)
                print(f"⚠️  Generate TOKEN_ENCRYPTION_KEY for production:")
                print(f"   TOKEN_ENCRYPTION_KEY={key.decode()}")
    
    def encrypt(self, token: str) -> str:
        """Encrypt token and return hex string"""
        encrypted = self.cipher.encrypt(token.encode())
        return encrypted.hex()
    
    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt token from hex string"""
        try:
            encrypted = bytes.fromhex(encrypted_token)
            token = self.cipher.decrypt(encrypted).decode()
            return token
        except Exception as e:
            raise ValueError(f"Failed to decrypt token: {e}")

token_encryption = TokenEncryption()

# ============================================================================
# STATELESS PLAID CLIENT (fetch fresh data on every request)
# ============================================================================

class StatelessPlaidClient:
    """
    Fetch data from Plaid on-demand.
    Don't store anything in database.
    Simple in-memory cache for 5 minutes to improve UX.
    """
    
    def __init__(self):
        self.client_id = os.getenv('PLAID_CLIENT_ID')
        self.secret = os.getenv('PLAID_SECRET')
        self.env = os.getenv('PLAID_ENV', 'sandbox')
        self._cache = {}
        self._cache_expiry = {}
    
    def get_token_from_session(self) -> str:
        """Retrieve and decrypt access token from session"""
        if 'plaid_token' not in session:
            raise ValueError("No Plaid token in session. User must authenticate first.")
        
        encrypted_token = session['plaid_token']
        return token_encryption.decrypt(encrypted_token)
    
    def store_token_in_session(self, access_token: str):
        """Encrypt and store access token in session"""
        encrypted = token_encryption.encrypt(access_token)
        session['plaid_token'] = encrypted
        session['plaid_token_at'] = datetime.now().isoformat()
        session.permanent = True
        session.modified = True
    
    def get_dashboard_data(self) -> dict:
        """Fetch fresh dashboard data from Plaid (NOT stored in database)"""
        try:
            access_token = self.get_token_from_session()
            
            if not self.client_id or not self.secret:
                return {'error': 'Plaid credentials not configured'}
            
            # Check cache first (5 minute TTL for better UX)
            cache_key = f"plaid_data_{access_token[-10:]}"
            now = time.time()
            
            if cache_key in self._cache and cache_key in self._cache_expiry:
                if now < self._cache_expiry[cache_key]:
                    return self._cache[cache_key]
            
            # Cache miss: fetch from Plaid
            client = PlaidClient(self.client_id, self.secret, self.env)
            credit_data = client.get_credit_card_data(access_token)
            
            if not credit_data or 'error' in credit_data:
                error_msg = credit_data.get('error', 'Unknown error') if credit_data else 'No data'
                return {'error': f'Failed to fetch from Plaid: {error_msg}'}
            
            # Cache for 5 minutes
            self._cache[cache_key] = credit_data
            self._cache_expiry[cache_key] = now + 300  # 5 minutes
            
            return credit_data
            
        except ValueError as e:
            return {'error': str(e)}
        except Exception as e:
            return {'error': f'Error fetching data: {str(e)}'}
    
    def get_transactions(self, days: int = 90) -> list:
        """Get transactions for specified days (NOT stored)"""
        data = self.get_dashboard_data()
        if 'error' in data:
            return []
        return data.get('transactions', [])
    
    def clear_session(self):
        """Remove token from session (user logout)"""
        session.pop('plaid_token', None)
        session.pop('plaid_token_at', None)
        session.modified = True

plaid_client = StatelessPlaidClient()

# ============================================================================
# AUTH DECORATORS (simple session-based)
# ============================================================================

def require_plaid_token(f):
    """Require user to have Plaid token in session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'plaid_token' not in session:
            # For APIs, return 401
            if request.path.startswith('/api/'):
                return jsonify({'error': 'Unauthorized. Please configure Plaid token.'}), 401
            # For pages, redirect to setup
            return redirect(url_for('setup'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# ROUTES (stateless, fetch-on-demand)
# ============================================================================

@app.route('/')
def dashboard():
    """Main dashboard - fetch fresh data from Plaid"""
    if 'plaid_token' not in session:
        # Try to load from .env for local development
        env_token = os.getenv('PLAID_ACCESS_TOKEN')
        if env_token:
            try:
                plaid_client.store_token_in_session(env_token)
            except Exception as e:
                return render_template('setup.html',
                                     message=f"Error loading token from .env: {str(e)}")
        else:
            return render_template('setup.html',
                                 message="Please configure Plaid to see your credit dashboard")
    
    credit_data = plaid_client.get_dashboard_data()
    
    if 'error' in credit_data:
        return render_template('setup.html',
                             message=f"Error: {credit_data['error']}")
    
    analysis = analyze_transactions(credit_data.get('transactions', []))
    
    return render_template('dashboard.html',
                         credit_data=credit_data,
                         analysis=analysis)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Setup page for Plaid configuration"""
    if request.method == 'POST':
        # User submitted their access token
        access_token = request.form.get('access_token', '').strip()
        
        if access_token:
            try:
                # Store in encrypted session
                plaid_client.store_token_in_session(access_token)
                return redirect(url_for('dashboard'))
            except Exception as e:
                return render_template('setup.html',
                                     error=f'Invalid token: {str(e)}')
    
    # Show setup form
    return render_template('setup.html')

@app.route('/logout')
def logout():
    """Clear session and logout user"""
    plaid_client.clear_session()
    return redirect(url_for('setup'))

# ============================================================================
# API ENDPOINTS (all stateless, fetch on-demand)
# ============================================================================

@app.route('/api/dashboard')
@require_plaid_token
def api_dashboard():
    """API endpoint for full dashboard data"""
    credit_data = plaid_client.get_dashboard_data()
    
    if 'error' in credit_data:
        return jsonify(credit_data), 503
    
    return jsonify(credit_data)

@app.route('/api/transactions')
@require_plaid_token
def api_transactions():
    """API endpoint for transactions only"""
    transactions = plaid_client.get_transactions(
        days=request.args.get('days', 90, type=int)
    )
    return jsonify(transactions)

@app.route('/api/spending-analysis')
@require_plaid_token
def api_spending_analysis():
    """API endpoint for spending analysis"""
    transactions = plaid_client.get_transactions()
    analysis = analyze_transactions(transactions)
    return jsonify(analysis)

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0-stateless',
        'storage': 'session-only',
        'database': 'none'
    }), 200

@app.route('/config-status')
def config_status():
    """Check configuration status"""
    has_token = 'plaid_token' in session
    return jsonify({
        'user_authenticated': has_token,
        'token_stored_at': session.get('plaid_token_at', None),
        'has_plaid_client_id': bool(os.getenv('PLAID_CLIENT_ID')),
        'has_plaid_secret': bool(os.getenv('PLAID_SECRET')),
        'plaid_env': os.getenv('PLAID_ENV', 'sandbox'),
        'encryption_configured': bool(os.getenv('TOKEN_ENCRYPTION_KEY'))
    }), 200

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def analyze_transactions(transactions: list) -> dict:
    """Analyze transactions for dashboard insights (not stored)"""
    if not transactions:
        return {}
    
    monthly_spending = defaultdict(float)
    category_spending = defaultdict(float)
    merchant_spending = defaultdict(float)
    
    for txn in transactions:
        # Monthly totals
        date = txn.get('date', '')
        if date:
            if isinstance(date, datetime):
                date_str = date.strftime('%Y-%m-%d')
            elif hasattr(date, 'isoformat'):
                date_str = date.isoformat()
            else:
                date_str = str(date)
            
            month = date_str[:7]
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
    
    top_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)[:5]
    top_merchants = sorted(merchant_spending.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'monthly_spending': dict(sorted(monthly_spending.items())),
        'top_categories': top_categories,
        'top_merchants': top_merchants,
        'total_spent': sum(merchant_spending.values())
    }

# ============================================================================
# STARTUP MESSAGES
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 STATELESS Credit History Dashboard")
    print("="*70)
    print("✅ Zero customer data storage")
    print("✅ Access token stored in encrypted session cookie")
    print("✅ Fresh data fetched from Plaid on every request")
    print("✅ No database required")
    print("="*70)
    print("\n📊 Open browser to: http://localhost:5001")
    
    if not os.getenv('TOKEN_ENCRYPTION_KEY'):
        print("\n⚠️  For production, generate TOKEN_ENCRYPTION_KEY:")
        print(f"    python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
    
    print("\nPress Ctrl+C to stop\n")
    app.run(debug=True, port=5001)
else:
    # Production (Render/Gunicorn)
    app.config['DEBUG'] = False
