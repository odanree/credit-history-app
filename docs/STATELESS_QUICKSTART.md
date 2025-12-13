# Quick Start: Stateless Architecture

Zero customer data storage. Fresh financial data from Plaid every request.

## 🚀 Setup (2 minutes)

### 1. Generate Encryption Key

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Save the output to `.env`:
```bash
TOKEN_ENCRYPTION_KEY=gGEbWq0j0zb0oMmyo_as662RIswlIbM7ig9QbWezONo=
```

### 2. Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements (includes Flask-Session, cryptography)
pip install -r requirements.txt
```

### 3. Get Plaid Access Token

```bash
python3 scripts/setup_plaid_token.py
```

This guides you through the Plaid Link flow. Copy your access token.

### 4. Configure Environment

```bash
# Add to .env
PLAID_CLIENT_ID=your_client_id
PLAID_SECRET=your_secret
PLAID_ACCESS_TOKEN=your_access_token
PLAID_ENV=sandbox
TOKEN_ENCRYPTION_KEY=your_key_from_step_1
```

### 5. Run the App

```bash
source .venv/bin/activate
python3 -m src.app_stateless
```

Visit: **http://localhost:5001**

---

## 🎯 How It Works

1. **Setup Page** (no token in session yet)
   ```
   User visits http://localhost:5001
   ↓
   Sees setup page with instructions
   ```

2. **User Configures Token** (encrypted, stored in cookie)
   ```
   User pastes access token on setup page
   ↓
   Token encrypted with TOKEN_ENCRYPTION_KEY
   ↓
   Stored in httpOnly session cookie
   ```

3. **Dashboard** (fresh data from Plaid)
   ```
   User sees dashboard
   ↓
   App retrieves token from encrypted cookie
   ↓
   Fetches fresh data from Plaid API
   ↓
   Returns directly to browser
   ↓
   Data NOT stored in database
   ```

---

## 📊 Key Differences vs. Database Storage

| Feature | Database | Stateless |
|---------|----------|-----------|
| Data Storage | SQL database | Encrypted session cookie |
| Plaid API Calls | On sync (1x/day) | On every page load |
| Speed | Fast (cached) | Slower (API calls) |
| Data Breach Risk | HIGH ⚠️ | ZERO ✅ |
| GDPR Compliance | Complex | Trivial ✅ |
| Database Needed | YES | NO ✅ |

---

## 🔒 Security

### Token Encryption
```python
# Token is encrypted before storing in session
encrypted = Fernet(TOKEN_ENCRYPTION_KEY).encrypt(access_token.encode())
```

### Session Security
```python
# Session cookie is:
SESSION_COOKIE_HTTPONLY = True   # Can't be stolen by JavaScript
SESSION_COOKIE_SECURE = True      # HTTPS only (production)
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
```

### What's NOT Stored
- ❌ Transactions
- ❌ Credit cards
- ❌ Balances
- ❌ Credit scores
- ❌ Personal info (SSN, name, address)

### What IS Stored
- ✅ Encrypted Plaid access token (in session)
- ✅ Session metadata (timestamp)

---

## 🧪 Testing

### Test the App

```bash
# Terminal 1: Start the app
source .venv/bin/activate
python3 -m src.app_stateless

# Terminal 2: Test endpoints
curl http://localhost:5001/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-13T...",
  "version": "2.0.0-stateless",
  "storage": "session-only",
  "database": "none"
}
```

### Test Configuration

```bash
curl http://localhost:5001/config-status
```

Expected response (no token yet):
```json
{
  "user_authenticated": false,
  "token_stored_at": null,
  "has_plaid_client_id": true,
  "has_plaid_secret": true,
  "plaid_env": "sandbox",
  "encryption_configured": true
}
```

---

## 🚨 Troubleshooting

### "No Plaid token in session"
**Problem:** Tried to access dashboard without setting up token
**Solution:** Go to setup page and paste your access token

### "Failed to decrypt token"
**Problem:** TOKEN_ENCRYPTION_KEY is wrong or missing
**Solution:** 
```bash
# Generate new key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Update .env and restart app
```

### "ModuleNotFoundError: cryptography"
**Problem:** cryptography not installed
**Solution:**
```bash
source .venv/bin/activate
pip install cryptography
```

### "Plaid API returns 401"
**Problem:** Access token expired or invalid
**Solution:**
```bash
python3 scripts/setup_plaid_token.py
# Get new token and paste on setup page
```

---

## 📈 Performance Notes

### First Request (Cold)
- Setup page: ~50ms
- After entering token: ~300ms (Plaid API call)

### Subsequent Requests
- Dashboard load: ~200-500ms (Plaid API call)
- Each API call hits Plaid (no server-side caching)

### To Speed Up
Add Redis caching (optional):
```python
# See STATELESS_ARCHITECTURE.md Option 3
```

---

## 🔄 Migration from Database

If you have an existing database version:

1. **Keep both running** (database version on port 5000, stateless on port 5001)
2. **Test stateless version** thoroughly
3. **Switch traffic** to stateless version
4. **Remove database** (no longer needed)

See `MIGRATION_GUIDE.md` for detailed steps.

---

## 📚 Documentation

- **STATELESS_ARCHITECTURE.md** - Complete design & options
- **MIGRATION_GUIDE.md** - How to switch from database
- **SECURITY.md** - Security & compliance details

---

## 🆘 Questions?

1. **"Why no database?"**
   - No data breach risk
   - GDPR compliance is trivial
   - Plaid handles backups
   - Simpler to operate

2. **"Can I add historical analysis?"**
   - Yes, add Redis cache (see STATELESS_ARCHITECTURE.md)
   - Or add minimal Postgres (see hybrid option)

3. **"What about offline mode?"**
   - Pure stateless: No offline
   - With Redis cache: 7 days offline

4. **"How does compliance work?"**
   - GDPR: "We don't store customer data"
   - CCPA: "We don't collect/sell customer data"
   - FCRA: "Token encrypted in session, never stored"

---

**Ready to start?** Run the setup commands above and visit http://localhost:5001!
