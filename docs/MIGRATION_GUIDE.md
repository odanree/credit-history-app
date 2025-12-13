# Migration Guide: From Database Storage to Stateless Architecture

## Overview

This guide shows how to migrate from storing customer data in SQL to the stateless model where:
- **Access tokens** stored in encrypted session cookies
- **Financial data** fetched fresh from Plaid on every request
- **Zero customer data** in your database
- **GDPR/CCPA compliance** is trivial (nothing to delete!)

---

## Quick Start (5 minutes)

### Step 1: Use Stateless App

```bash
# Current (with database)
python -m src.app

# Switch to Stateless (no database)
python -m src.app_stateless
```

### Step 2: Set Environment Variables

```bash
# Required for encryption
TOKEN_ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Add to .env
echo "TOKEN_ENCRYPTION_KEY=$TOKEN_ENCRYPTION_KEY" >> .env
```

### Step 3: That's it!

No database setup needed. Session cookie handles everything.

---

## What Changed?

### Before (Database Storage)
```python
# app.py - stored data in database
@app.route('/dashboard')
def dashboard():
    user = User.query.get(session['user_id'])  # Query database
    txns = Transaction.query.filter_by(user_id=user.id).all()  # All transactions stored
    cards = CreditCard.query.filter_by(user_id=user.id).all()  # All credit cards stored
    
    return render_template('dashboard.html', transactions=txns, cards=cards)
```

**Problems:**
- ❌ Customer data stored in database
- ❌ Data breach = user info exposed
- ❌ GDPR requests = must export/delete from database
- ❌ Database maintenance required
- ❌ Backups contain sensitive data

### After (Stateless)
```python
# app_stateless.py - fetch fresh from Plaid
@app.route('/')
def dashboard():
    plaid_client = StatelessPlaidClient()
    credit_data = plaid_client.get_dashboard_data()  # Fresh from Plaid
    
    return render_template('dashboard.html', credit_data=credit_data)
    # Data not stored - returned directly to browser
```

**Benefits:**
- ✅ Zero customer data stored
- ✅ Data breach = token exposed (can be revoked)
- ✅ GDPR requests = "We don't store your data"
- ✅ No database maintenance
- ✅ Backups only contain subscription info

---

## Migration Path

### Phase 1: Deploy Stateless App Alongside Current App (Week 1)

```bash
# Keep current app.py working
# Deploy new app_stateless.py on a test port

# config/wsgi.py
import os
from src.app import app as current_app
from src.app_stateless import app as stateless_app

# Use environment variable to switch
if os.getenv('USE_STATELESS'):
    app = stateless_app
else:
    app = current_app
```

Test the new stateless version before switching.

### Phase 2: Redirect Users to Stateless App (Week 2)

```bash
# config/wsgi.py
from src.app_stateless import app  # Stateless is now primary
```

- Existing users: Sessions continue to work
- New users: Use stateless architecture
- Monitor for issues

### Phase 3: Archive Old Database (Week 3)

```bash
# Once confident, disable database
# Export any subscription/billing data to separate storage

# Delete customer data tables
DROP TABLE transactions;
DROP TABLE credit_cards;
DROP TABLE credit_reports;
DROP TABLE audit_logs;

# Keep only:
# - Users (subscription info)
# - Sessions (if using server-side sessions)
```

### Phase 4: Full Cutover (Week 4)

```bash
# Remove old app.py and database
# Stateless is now production
# No customer data storage needed
```

---

## Database Changes

### What To Keep

```sql
-- Minimal database (subscription/billing only)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    subscription_tier VARCHAR(50),      -- free, pro, enterprise
    created_at TIMESTAMP,
    updated_at TIMESTAMP
    -- NO financial data
    -- NO personal data
    -- NO transactions
);

CREATE TABLE sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP,
    expires_at TIMESTAMP
    -- Session metadata only
    -- Access token is in encrypted cookie, not here
);
```

### What To Delete

```sql
-- Delete these tables (data not needed)
DROP TABLE transactions;
DROP TABLE credit_cards;
DROP TABLE credit_reports;
DROP TABLE audit_logs;
DROP TABLE plaid_accounts;  -- Token in session instead
```

---

## Code Comparison

### Session Management

**Before:**
```python
# app.py
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

class User(db.Model):
    id = Column(UUID)
    transactions = relationship('Transaction')
    # 1000+ customer records in database
```

**After:**
```python
# app_stateless.py
from flask_session import Session
Session(app)

# Session in encrypted cookie
# Zero database storage
```

### Fetching Data

**Before:**
```python
def get_transactions(user_id):
    # Query database
    return Transaction.query.filter_by(user_id=user_id).all()
    # Returns 3000+ stored transactions
```

**After:**
```python
def get_transactions(user_id):
    # Fetch from Plaid on-demand
    access_token = session['plaid_token']
    return plaid_client.transactions_get(access_token)
    # Returns fresh data, not stored
```

### Authentication

**Before:**
```python
@app.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(email=email).first()
    if user and verify_password(user.password_hash, password):
        session['user_id'] = user.id
        db.session.commit()
```

**After:**
```python
@app.route('/setup', methods=['POST'])
def setup():
    access_token = request.form.get('access_token')
    plaid_client.store_token_in_session(access_token)
    # Token encrypted and stored in cookie
```

### GDPR Deletion

**Before:**
```python
@app.route('/api/delete-me', methods=['DELETE'])
def delete_account(user_id):
    # Delete from multiple tables
    User.query.filter_by(id=user_id).delete()
    Transaction.query.filter_by(user_id=user_id).delete()
    CreditCard.query.filter_by(user_id=user_id).delete()
    CreditReport.query.filter_by(user_id=user_id).delete()
    PlaidAccount.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    # Complex data management
```

**After:**
```python
@app.route('/api/delete-me', methods=['DELETE'])
def delete_account(user_id):
    # Delete minimal data
    User.query.filter_by(id=user_id).delete()  # Just subscription info
    session.clear()  # Clear encrypted cookie
    # Done! No financial data to manage
```

---

## Performance Comparison

### Request Latency

| Operation | Database | Stateless |
|-----------|----------|-----------|
| Load Dashboard | 50-100ms (DB query) | 200-500ms (Plaid API) |
| Filter Transactions | 30-50ms (DB query) | 200-500ms (Plaid API) |
| Calculate Spending | 10-20ms (in memory) | 5-10ms (in memory) |

**Trade-off:** Slightly slower, but:
- Data always fresh
- No data breach risk
- No GDPR liability

### Solution: Add Redis Cache

If performance is concern, use **hybrid approach**:

```python
class HybridPlaidClient:
    """Stateless with optional Redis cache"""
    
    def get_transactions(self, access_token, use_cache=True):
        # Try cache first (7-day TTL)
        cache_key = f"txns:{user_id}"
        cached = redis.get(cache_key)
        if cached and use_cache:
            return json.loads(cached)  # Fast!
        
        # Cache miss: fetch from Plaid
        txns = plaid_client.transactions_get(access_token)
        
        # Cache for 7 days (auto-expires)
        redis.setex(cache_key, 7*24*3600, json.dumps(txns))
        return txns
```

**Result:**
- First request: 200-500ms (Plaid API)
- Subsequent requests: 5-10ms (Redis cache)
- 7-day auto-expiration (GDPR-friendly)

---

## Testing

### Test Stateless App Locally

```bash
# Install Flask-Session dependency
pip install Flask-Session

# Run stateless version
python -m src.app_stateless

# Visit: http://localhost:5001
# You'll see setup page (no token in session yet)

# Get a test Plaid token
python scripts/setup_plaid_token.py

# Enter token on setup page
# Dashboard now shows fresh data from Plaid
```

### Run Tests

```bash
# Tests still work (they mock Plaid API)
pytest tests/

# All tests pass regardless of app version
# Tests don't depend on database/session setup
```

---

## Deployment

### Render Deployment

**Before:**
```yaml
# render.yaml
services:
  - type: web
    env: python
  - type: postgres  # Required for database
    ipAllowList: []
```

**After:**
```yaml
# render.yaml
services:
  - type: web
    env: python
    # NO DATABASE REQUIRED!

envVars:
  - key: USE_STATELESS
    value: "true"
  - key: TOKEN_ENCRYPTION_KEY
    generateValue: true
```

**Benefits:**
- ✅ No database server needed
- ✅ No database backups
- ✅ Lower Render bill
- ✅ Simpler deployment

### Environment Variables

```bash
# Add to .env and Render
FLASK_SECRET_KEY=<generate-new>
TOKEN_ENCRYPTION_KEY=<generate-new>
PLAID_CLIENT_ID=<from-plaid>
PLAID_SECRET=<from-plaid>
PLAID_ENV=sandbox

# Remove (not needed)
DATABASE_URL  # No database!
```

---

## Rollback Plan

If stateless doesn't work, rollback is simple:

```bash
# Revert to database version
git checkout src/app.py
python -m src.app

# Sessions in database still work
# Users don't notice a change
```

---

## Migration Checklist

- [ ] Create TOKEN_ENCRYPTION_KEY
- [ ] Install Flask-Session: `pip install Flask-Session`
- [ ] Deploy app_stateless.py to test environment
- [ ] Test setup flow: configure token, view dashboard
- [ ] Test filtering and analysis features
- [ ] Verify health check endpoints
- [ ] Load test with simulated users
- [ ] Switch production to app_stateless
- [ ] Monitor for issues (week 1)
- [ ] Archive old database tables
- [ ] Remove database from Render
- [ ] Update documentation
- [ ] Delete app.py (old database version)

---

## FAQ

### Q: What if Plaid is down?

**A:** Stateless app won't work (can't fetch data). Options:
1. Add Redis cache (7-day data available offline)
2. Show cached data with "data is 7 days old" warning
3. Show status page: "Plaid is temporarily unavailable"

### Q: Can users access their data offline?

**A:** No with pure stateless, but with Redis cache:
- First 7 days: Cached data available
- After 7 days: Must reconnect to Plaid

### Q: What about historical trend analysis?

**A:** Options:
1. **Pure stateless**: No trends (show only 90-day history from Plaid)
2. **Hybrid**: Cache for 7+ days, calculate trends from cache
3. **Lite database**: Store aggregated metrics only, not raw transactions

### Q: Is session cookie secure?

**A:** Yes! With these settings:
```python
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Can't be stolen by JavaScript
app.config['SESSION_COOKIE_SECURE'] = True     # HTTPS only
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # CSRF protection
```

### Q: Can I still do compliance audits?

**A:** Yes, better than before!
- Audit log: "User X accessed their data at 2:30pm"
- Nothing else to audit (no stored data)
- GDPR/CCPA compliance: "We don't store customer data"

### Q: How do I demo to investors?

**A:** Say:
- "Zero data breach risk"
- "GDPR compliant by design"
- "No database maintenance"
- "HIPAA-ready architecture"
- "SOC 2 path is clear"

---

## Next Steps

1. **Try it out locally:**
   ```bash
   pip install Flask-Session cryptography
   python -m src.app_stateless
   ```

2. **Test the setup flow:**
   - Get Plaid token: `python scripts/setup_plaid_token.py`
   - Enter token on setup page
   - View fresh data from Plaid

3. **Compare with current app:**
   - Run both versions
   - Feel the difference (fresh vs. cached data)

4. **Deploy to test environment:**
   - Create new Render instance for testing
   - Use app_stateless.py
   - Verify works in production environment

5. **Plan migration:**
   - Week 1: Deploy alongside current app
   - Week 2: Redirect traffic to stateless
   - Week 3: Remove database
   - Week 4: Full cutover

---

## Support

**Questions?**
- Check STATELESS_ARCHITECTURE.md for design details
- Review app_stateless.py for implementation
- Run tests: `pytest tests/`

**Issues?**
- Plaid token errors: Run `python scripts/setup_plaid_token.py`
- Encryption errors: Verify TOKEN_ENCRYPTION_KEY is set
- Session errors: Check Flask-Session is installed
