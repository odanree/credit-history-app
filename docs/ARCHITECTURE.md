# Multi-Tenant Credit Monitoring System - Architecture Design

## 📋 System Overview

Transform the credit-history-app from a single-user tool into a production-ready multi-tenant SaaS platform where users can securely connect their own bank accounts and credit data.

### Core Principles
- **Security First**: Encrypted credentials, secure token handling, data isolation
- **Privacy**: GDPR/CCPA compliant, user consent management, audit logs
- **Scalability**: Database-backed architecture, per-user data isolation
- **User Experience**: Seamless Plaid Link integration, intuitive dashboard

---

## 🏗️ Architecture Layers

### 1. Authentication & User Management Layer

#### Database Schema
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- bcrypt hashed
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),  -- For 2FA setup
    consent_given_at TIMESTAMP,  -- GDPR consent tracking
    deleted_at TIMESTAMP  -- Soft delete for GDPR
);

-- User sessions table
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    access_token VARCHAR(500) UNIQUE NOT NULL,
    refresh_token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45),  -- IPv4 or IPv6
    user_agent TEXT,
    is_valid BOOLEAN DEFAULT TRUE
);

-- Audit log table
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,  -- login, logout, data_accessed, etc
    resource_type VARCHAR(50),  -- user, plaid_account, transaction
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Authentication Flow
```
User Registration/Login
    ↓
Password validation (bcrypt)
    ↓
Generate JWT tokens (access + refresh)
    ↓
Store in user_sessions + Redis cache
    ↓
Set secure httpOnly cookies
    ↓
Return to frontend
```

#### Key Components
- **Password Hashing**: bcrypt with salt rounds = 12
- **JWT Tokens**: 
  - Access token: 15 minutes expiry
  - Refresh token: 7 days expiry
- **Session Storage**: Redis for performance, DB for persistence
- **MFA**: TOTP (Time-based OTP) optional for users

### 2. Plaid Integration Layer (Multi-Account per User)

#### Database Schema
```sql
-- Plaid accounts linked by users
CREATE TABLE plaid_accounts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plaid_item_id VARCHAR(255) UNIQUE NOT NULL,
    plaid_access_token TEXT NOT NULL ENCRYPTED,  -- Use pgcrypto
    bank_name VARCHAR(255),
    account_name VARCHAR(255),
    account_type VARCHAR(50),  -- credit, checking, savings
    last_synced TIMESTAMP,
    sync_status VARCHAR(20),  -- success, pending, error
    error_message TEXT,
    requires_reauth BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

-- Transaction cache (updated on sync)
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    plaid_account_id UUID REFERENCES plaid_accounts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plaid_transaction_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    amount DECIMAL(12, 2),
    category VARCHAR(100),
    date DATE NOT NULL,
    merchant_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_date (user_id, date)
);

-- Credit reports (cached from Experian)
CREATE TABLE credit_reports (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    credit_score INT,
    report_date DATE,
    experian_report_id VARCHAR(255),
    raw_report JSONB,  -- Store full report for reference
    created_at TIMESTAMP DEFAULT NOW()
);

-- Data retention policy tracking
CREATE TABLE data_retention (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    data_type VARCHAR(50),  -- transaction, credit_report
    days_to_retain INT DEFAULT 90,
    last_purge_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Plaid Link Frontend Flow
```javascript
// User clicks "Connect Bank Account"
    ↓
Frontend loads Plaid Link SDK
    ↓
User selects bank and logs in
    ↓
Plaid returns public_token
    ↓
Frontend sends public_token to backend /api/plaid/exchange
    ↓
Backend exchanges for access_token via Plaid API
    ↓
Backend encrypts & stores access_token in plaid_accounts table
    ↓
Trigger initial data sync
    ↓
Dashboard shows new account
```

#### Token Encryption
```python
# Use django-cryptography or pgcrypto
from cryptography.fernet import Fernet
import os

ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')  # Rotate periodically
cipher = Fernet(ENCRYPTION_KEY)

# Store encrypted
encrypted_token = cipher.encrypt(access_token.encode())
db.plaid_accounts.update(
    id=account_id,
    plaid_access_token=encrypted_token
)

# Retrieve and decrypt
encrypted = db.plaid_accounts.get(id=account_id).plaid_access_token
access_token = cipher.decrypt(encrypted).decode()
```

### 3. Data Synchronization Layer

#### Sync Architecture
```
Background Job (Celery/APScheduler)
    ↓
For each user:
    ↓
  For each plaid_account:
    ↓
    Fetch transactions (last 30 days + new)
    Fetch account balances
    Check for reauth required errors
    ↓
    Store in transactions table
    Update last_synced timestamp
    ↓
  Fetch credit report (monthly)
    ↓
    Store in credit_reports table
    ↓
  Clean up old data (30/90 day retention)
```

#### Sync Implementation
```python
# models/sync.py
class DataSync:
    @celery_task
    def sync_all_users():
        """Sync all user accounts every 6 hours"""
        for user in User.query.filter(is_active=True):
            sync_user_data.delay(user.id)
    
    @celery_task
    def sync_user_data(user_id):
        """Sync all accounts for a user"""
        user = User.get(user_id)
        
        for account in user.plaid_accounts:
            try:
                # Decrypt token
                access_token = decrypt(account.plaid_access_token)
                
                # Fetch transactions
                client = PlaidClient(...)
                transactions = client.get_transactions(
                    access_token,
                    start_date=account.last_synced or date.today() - timedelta(days=30)
                )
                
                # Handle ITEM_LOGIN_REQUIRED error
                if 'error_code' in transactions and transactions['error_code'] == 'ITEM_LOGIN_REQUIRED':
                    account.requires_reauth = True
                    account.save()
                    notify_user_reauth_required(user, account)
                    continue
                
                # Store transactions
                for txn in transactions['transactions']:
                    Transaction.create_or_update(
                        user_id=user_id,
                        plaid_account_id=account.id,
                        plaid_transaction_id=txn['transaction_id'],
                        name=txn['name'],
                        amount=txn['amount'],
                        date=txn['date'],
                        category=txn['category'][0] if txn.get('category') else 'Other'
                    )
                
                account.last_synced = datetime.now()
                account.sync_status = 'success'
                account.save()
                
            except Exception as e:
                account.sync_status = 'error'
                account.error_message = str(e)
                account.save()
                log_error(user_id, account.id, str(e))
```

### 4. API Layer (User-Facing Endpoints)

#### Authentication Endpoints
```python
# routes/auth.py
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    
    # Validate email uniqueness
    if User.query.filter_by(email=data['email']).first():
        return {'error': 'Email already exists'}, 409
    
    # Hash password
    user = User(
        email=data['email'],
        password_hash=bcrypt.hashpw(data['password']),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        consent_given_at=datetime.now()  # GDPR consent
    )
    db.session.add(user)
    db.session.commit()
    
    # Generate tokens
    tokens = generate_tokens(user.id)
    audit_log('user_registered', 'user', user.id)
    
    return {
        'user_id': user.id,
        'access_token': tokens['access'],
        'refresh_token': tokens['refresh']
    }, 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not bcrypt.verify(data['password'], user.password_hash):
        audit_log('login_failed', 'user', email=data['email'])
        return {'error': 'Invalid credentials'}, 401
    
    # Check MFA if enabled
    if user.mfa_enabled:
        # Return challenge, wait for TOTP verification
        pass
    
    tokens = generate_tokens(user.id)
    user.last_login = datetime.now()
    db.session.commit()
    
    audit_log('user_login', 'user', user.id)
    
    return {
        'user_id': user.id,
        'access_token': tokens['access'],
        'refresh_token': tokens['refresh']
    }, 200

@app.route('/api/auth/refresh', methods=['POST'])
def refresh():
    """Refresh access token"""
    data = request.json
    session = UserSession.query.filter_by(
        refresh_token=data['refresh_token'],
        is_valid=True
    ).first()
    
    if not session or session.expires_at < datetime.now():
        return {'error': 'Invalid or expired refresh token'}, 401
    
    tokens = generate_tokens(session.user_id)
    return tokens, 200

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout(user_id):
    """Logout user"""
    token = request.headers.get('Authorization').split(' ')[1]
    session = UserSession.query.filter_by(access_token=token).first()
    session.is_valid = False
    db.session.commit()
    
    audit_log('user_logout', 'user', user_id)
    return {'message': 'Logged out'}, 200
```

#### Plaid Integration Endpoints
```python
# routes/plaid.py
@app.route('/api/plaid/link-token', methods=['POST'])
@require_auth
def get_link_token(user_id):
    """Get Plaid Link token for frontend"""
    user = User.get(user_id)
    
    client = PlaidClient(...)
    response = client.create_link_token(
        user_id=user_id,
        client_name='Credit Monitor',
        user={'client_user_id': user_id},
        country_codes=['US'],
        language='en'
    )
    
    return {'link_token': response['link_token']}, 200

@app.route('/api/plaid/exchange-token', methods=['POST'])
@require_auth
def exchange_token(user_id):
    """Exchange public token for access token"""
    data = request.json
    
    client = PlaidClient(...)
    response = client.exchange_public_token(data['public_token'])
    
    # Store encrypted access token
    account = PlaidAccount(
        user_id=user_id,
        plaid_item_id=response['item_id'],
        plaid_access_token=encrypt(response['access_token']),
        bank_name='Unknown',  # Will update on first sync
        sync_status='pending'
    )
    db.session.add(account)
    db.session.commit()
    
    # Trigger initial sync
    sync_user_data.delay(user_id)
    
    audit_log('plaid_account_connected', 'plaid_account', account.id)
    
    return {
        'account_id': account.id,
        'item_id': account.plaid_item_id
    }, 201

@app.route('/api/plaid/accounts', methods=['GET'])
@require_auth
def get_plaid_accounts(user_id):
    """Get all linked Plaid accounts for user"""
    accounts = PlaidAccount.query.filter_by(user_id=user_id).all()
    
    return {
        'accounts': [{
            'id': a.id,
            'bank_name': a.bank_name,
            'account_name': a.account_name,
            'sync_status': a.sync_status,
            'last_synced': a.last_synced.isoformat(),
            'requires_reauth': a.requires_reauth
        } for a in accounts]
    }, 200

@app.route('/api/plaid/reauth/<account_id>', methods=['POST'])
@require_auth
def reauth_account(user_id, account_id):
    """Get update link token for account reauth"""
    account = PlaidAccount.query.get(account_id)
    
    if account.user_id != user_id:
        return {'error': 'Unauthorized'}, 403
    
    client = PlaidClient(...)
    response = client.create_link_token(
        user_id=user_id,
        item_id=account.plaid_item_id,
        user={'client_user_id': user_id}
    )
    
    return {'link_token': response['link_token']}, 200
```

#### Dashboard Data Endpoints
```python
# routes/dashboard.py
@app.route('/api/dashboard/summary', methods=['GET'])
@require_auth
def get_dashboard_summary(user_id):
    """Get summary for all accounts"""
    accounts = PlaidAccount.query.filter_by(user_id=user_id).all()
    
    total_balance = sum(a.get_current_balance() for a in accounts)
    total_limit = sum(a.get_credit_limit() for a in accounts)
    
    # Get latest credit score
    latest_credit = CreditReport.query.filter_by(
        user_id=user_id
    ).order_by(CreditReport.created_at.desc()).first()
    
    return {
        'total_balance': total_balance,
        'total_limit': total_limit,
        'utilization': (total_balance / total_limit * 100) if total_limit > 0 else 0,
        'credit_score': latest_credit.credit_score if latest_credit else None,
        'accounts_count': len(accounts),
        'last_synced': max(a.last_synced for a in accounts) if accounts else None
    }, 200

@app.route('/api/dashboard/transactions', methods=['GET'])
@require_auth
def get_transactions(user_id):
    """Get filtered transactions"""
    # Query params: days=30, category=Food, limit=50, offset=0
    days = request.args.get('days', 30, type=int)
    category = request.args.get('category')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    start_date = datetime.now() - timedelta(days=days)
    
    query = Transaction.query.filter_by(user_id=user_id).filter(
        Transaction.date >= start_date
    )
    
    if category:
        query = query.filter_by(category=category)
    
    transactions = query.order_by(Transaction.date.desc()).limit(limit).offset(offset).all()
    total = query.count()
    
    return {
        'transactions': [{
            'id': t.id,
            'name': t.name,
            'amount': t.amount,
            'category': t.category,
            'date': t.date.isoformat(),
            'merchant': t.merchant_name
        } for t in transactions],
        'total': total,
        'limit': limit,
        'offset': offset
    }, 200

@app.route('/api/dashboard/categories', methods=['GET'])
@require_auth
def get_spending_by_category(user_id):
    """Get spending breakdown by category"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)
    
    categories = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total')
    ).filter_by(user_id=user_id).filter(
        Transaction.date >= start_date
    ).group_by(Transaction.category).all()
    
    return {
        'categories': [{
            'name': c[0],
            'amount': float(c[1])
        } for c in categories]
    }, 200
```

### 5. Frontend Layer

#### Architecture
```
React/Vue.js SPA
├── Auth Pages
│   ├── Register
│   ├── Login
│   ├── MFA Setup
│   └── Password Reset
├── Plaid Integration
│   ├── Connect Bank Modal
│   ├── Reauth Modal
│   └── Account Management
└── Dashboard
    ├── Summary Cards
    ├── Transaction Filters (existing)
    ├── Spending Simulator (existing)
    ├── Multiple Account Tabs
    └── Data Export
```

#### Key Components
```javascript
// Services/api.js
class ApiService {
  async register(email, password, firstName, lastName) {
    return fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, firstName, lastName })
    }).then(r => r.json());
  }

  async login(email, password) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    }).then(r => r.json());
    
    // Store tokens securely
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    return response;
  }

  async getLinkToken() {
    return this.authenticatedFetch('/api/plaid/link-token', { method: 'POST' });
  }

  async exchangePlaidToken(publicToken) {
    return this.authenticatedFetch('/api/plaid/exchange-token', {
      method: 'POST',
      body: JSON.stringify({ public_token: publicToken })
    });
  }

  async getTransactions(days = 30, category = null) {
    const params = new URLSearchParams();
    params.append('days', days);
    if (category) params.append('category', category);
    
    return this.authenticatedFetch(`/api/dashboard/transactions?${params}`);
  }

  async authenticatedFetch(url, options = {}) {
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    };
    
    let response = await fetch(url, { ...options, headers });
    
    // Handle token refresh
    if (response.status === 401) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        response = await fetch(url, { ...options, headers: {
          ...headers,
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }});
      }
    }
    
    return response.json();
  }

  async refreshToken() {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: localStorage.getItem('refresh_token') })
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      return true;
    }
    
    // Refresh failed, redirect to login
    window.location.href = '/login';
    return false;
  }
}

// Components/PlaidLink.jsx
import { usePlaidLink } from 'react-plaid-link';

function PlaidLinkComponent() {
  const [linkToken, setLinkToken] = useState(null);

  useEffect(() => {
    ApiService.getLinkToken().then(data => setLinkToken(data.link_token));
  }, []);

  const { open, ready } = usePlaidLink({
    token: linkToken,
    onSuccess: (publicToken) => {
      ApiService.exchangePlaidToken(publicToken).then(() => {
        // Refresh dashboard
        window.location.reload();
      });
    }
  });

  return (
    <button onClick={() => open()} disabled={!ready}>
      Connect Bank Account
    </button>
  );
}
```

### 6. Security & Compliance

#### Data Protection
```
Frontend ──HTTPS──> Backend ──TLS──> Database
  ↓
- Tokens in httpOnly cookies (not localStorage)
- CSRF protection on state-changing endpoints
- Rate limiting on auth endpoints
- Input validation & sanitization
- SQL injection prevention (ORM)
```

#### Privacy Measures
```
1. GDPR Compliance
   - Explicit consent before data collection
   - Right to access: /api/user/export endpoint
   - Right to delete: /api/user/delete endpoint
   - Data retention policy: Delete after 90 days (configurable)

2. CCPA Compliance
   - Privacy policy linked during signup
   - Do Not Sell My Personal Information option
   - Easy deletion mechanism

3. Encryption
   - At rest: pgcrypto for Plaid tokens
   - In transit: TLS 1.3
   - Keys: Rotate every 90 days

4. Audit Logging
   - Log all data access
   - Log all data mutations
   - Log authentication events
   - 1 year retention for audit logs
```

#### Endpoints
```python
# routes/user.py
@app.route('/api/user/export', methods=['GET'])
@require_auth
def export_user_data(user_id):
    """GDPR right to access"""
    user = User.get(user_id)
    
    # Generate ZIP with:
    # - User profile
    # - All transactions (CSV)
    # - All credit reports (JSON)
    # - Audit logs
    
    audit_log('data_export', 'user', user_id)
    return send_file(zip_path, as_attachment=True)

@app.route('/api/user/delete', methods=['POST'])
@require_auth
def delete_user_account(user_id):
    """GDPR right to delete"""
    # Soft delete: mark user as deleted
    user = User.get(user_id)
    user.deleted_at = datetime.now()
    
    # Schedule hard delete in 30 days
    schedule_hard_delete(user_id, days=30)
    
    # Notify user
    send_deletion_email(user.email)
    
    audit_log('account_deleted', 'user', user_id)
    return {'message': 'Account scheduled for deletion'}, 200

@app.route('/api/user/consent', methods=['POST'])
@require_auth
def update_consent(user_id):
    """Manage consent preferences"""
    data = request.json
    user = User.get(user_id)
    user.consent_given_at = datetime.now() if data['consent'] else None
    db.session.commit()
    
    return {'consent': data['consent']}, 200
```

---

## 🗄️ Database Schema Summary

```
Users (auth)
├── user_sessions (token management)
├── audit_logs (compliance)
├── plaid_accounts (bank connections)
│   ├── transactions (cached data)
│   └── credit_reports (synced data)
└── data_retention (GDPR policies)
```

---

## 🔄 Data Flow Diagram

```
User Signup/Login
    ↓
[JWT Tokens + Session]
    ↓
Click "Connect Bank"
    ↓
[Plaid Link Modal]
    ↓
User selects bank + logs in
    ↓
[Public Token from Plaid]
    ↓
POST /api/plaid/exchange-token
    ↓
[Encrypt + Store Access Token]
    ↓
Trigger Background Sync (Celery)
    ↓
Fetch Transactions + Credit Data
    ↓
Store in Database
    ↓
Dashboard Updates Automatically
```

---

## 📈 Scaling Considerations

### Database
- PostgreSQL with partitioning on transactions (by user_id + date)
- Redis for session/cache layer
- Read replicas for analytics queries

### Backend
- Horizontal scaling with load balancer
- Celery workers for background jobs
- API rate limiting per user

### Frontend
- CDN for static assets
- Code splitting by route
- Service worker for offline support

---

## 🚀 Implementation Roadmap

**Phase 1: Authentication (Week 1-2)**
- [ ] User registration/login
- [ ] JWT token generation
- [ ] Session management
- [ ] Basic audit logging

**Phase 2: Plaid Integration (Week 2-3)**
- [ ] Plaid Link flow
- [ ] Token exchange & encryption
- [ ] Single account connection
- [ ] Initial sync logic

**Phase 3: Multi-Account & Sync (Week 3-4)**
- [ ] Multiple accounts per user
- [ ] Background sync jobs
- [ ] Error handling (reauth flow)
- [ ] Transaction caching

**Phase 4: Frontend & Dashboard (Week 4-5)**
- [ ] Auth UI (register, login, MFA)
- [ ] Plaid Link modal
- [ ] Multi-account dashboard
- [ ] Account management

**Phase 5: Privacy & Compliance (Week 5-6)**
- [ ] Data export endpoint
- [ ] Account deletion
- [ ] Audit logs UI
- [ ] Privacy policy

**Phase 6: Testing & Deployment (Week 6-7)**
- [ ] Integration tests
- [ ] Load testing
- [ ] Security audit
- [ ] Production deployment

---

## 🔐 Security Checklist

- [ ] HTTPS everywhere (TLS 1.3)
- [ ] Password hashing (bcrypt, 12+ rounds)
- [ ] Token rotation (refresh tokens)
- [ ] Rate limiting (auth endpoints)
- [ ] CSRF protection
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] Encryption at rest (pgcrypto)
- [ ] Audit logging (all access)
- [ ] Data retention policies
- [ ] GDPR/CCPA compliance
- [ ] Secure token storage (httpOnly cookies)
- [ ] MFA support
- [ ] Incident response plan

---

## 📊 Monitoring & Observability

```python
# Metrics to track
- Auth failures per IP (detect brute force)
- Sync success/failure rates
- API response times
- Token refresh rate
- Data export frequency
- Account deletion requests
- Error rates by endpoint
- Plaid API quota usage
```

---

## 📝 Notes

This architecture supports:
- **Security**: Industry-standard encryption, secure token handling, audit logs
- **Privacy**: GDPR/CCPA compliant, data export/deletion, consent management
- **Scalability**: Database partitioning, background jobs, caching strategies
- **UX**: Seamless Plaid integration, multi-account support, error recovery
- **Compliance**: Audit trails, data retention, regulatory requirements

Each phase builds on previous phases and can be deployed independently.
