# Credit History Application

[![codecov](https://codecov.io/gh/odanree/credit-history-app/branch/main/graph/badge.svg)](https://codecov.io/gh/odanree/credit-history-app)
[![Tests](https://github.com/odanree/credit-history-app/workflows/Pull%20Request%20CI/badge.svg)](https://github.com/odanree/credit-history-app/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive credit monitoring application integrating Plaid (transaction data) and Experian (credit reports).

## 🏗️ Architecture Options

Choose your approach based on your needs:

| Option | Storage | Speed | GDPR | Best For |
|--------|---------|-------|------|----------|
| **Stateless** | Session only | ~200ms | Trivial ✅ | MVP, low liability |
| **Hybrid** | Redis cache + minimal DB | ~10ms | Easy ✅ | Production, scale |
| **Traditional** | Full database | ~5ms | Complex | Analytics, trends |

**Quick recommendation:**
- **MVP/Proof of concept** → Use stateless (see [docs/STATELESS_QUICKSTART.md](docs/STATELESS_QUICKSTART.md))
- **Production app** → Use hybrid (see [docs/STATELESS_ARCHITECTURE.md](docs/STATELESS_ARCHITECTURE.md), Option 4)
- **Complex analytics** → Use traditional (see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md))

## 🚀 Quick Start

### Option 1: Stateless (Recommended for MVP)

Zero customer data storage. Fresh financial data from Plaid every request.

```bash
# Activate virtual environment
source .venv/bin/activate
python3 -m venv .venv  # First time only

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with Plaid credentials

# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add TOKEN_ENCRYPTION_KEY to .env

# Run stateless app
python3 -m src.app_stateless
```

Visit: http://localhost:5001

See [docs/STATELESS_QUICKSTART.md](docs/STATELESS_QUICKSTART.md) for detailed setup.

### Option 2: Traditional Database (Database storage)

```bash
# Same setup as above, but run:
python3 -m src.app
```

Visit: http://localhost:5001

## 📁 Project Structure

```
credit-history-app/
├── src/                      # Source code
│   ├── integrations/        # API integrations
│   │   ├── plaid_integration.py
│   │   └── experian_integration.py
│   ├── templates/           # Flask templates
│   │   ├── dashboard.html   # Main credit dashboard
│   │   └── setup.html       # Initial setup/configuration page
│   ├── app.py              # Flask web dashboard (traditional)
│   ├── app_stateless.py    # Flask web dashboard (stateless, no DB)
│   └── main.py             # Combined API client
├── scripts/                 # Utility scripts
│   ├── setup_plaid_token.py
│   └── run_plaid_only.py
├── tests/                   # Test files
│   └── test_*.py
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment variables
├── README.md                # This file - overview & quick start
├── SECURITY.md              # Security & vulnerability disclosure
├── docs/                    # Detailed documentation
│   ├── README.md           # Full setup & configuration guide
│   ├── ARCHITECTURE.md     # Multi-tenant database design
│   ├── STATELESS_ARCHITECTURE.md # Zero-storage options
│   ├── MIGRATION_GUIDE.md  # Migrate to stateless
│   ├── SECURITY_ANALYSIS.md # Detailed security review
│   ├── STATELESS_QUICKSTART.md # Stateless quick start
│   ├── DEPLOYMENT.md       # Deploy to Render
│   ├── CONTRIBUTING.md     # Development workflow
│   └── WORKFLOW.md         # Git workflow guide
└── .github/                 # GitHub configs
    └── copilot-instructions.md
```

## 📚 Documentation

- **[docs/STATELESS_QUICKSTART.md](docs/STATELESS_QUICKSTART.md)** - Quick start for stateless architecture (MVP)
- **[docs/STATELESS_ARCHITECTURE.md](docs/STATELESS_ARCHITECTURE.md)** - Design options: Session-only, Plaid-as-DB, Hybrid
- **[docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)** - Migrate from database to stateless
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Traditional multi-tenant database architecture
- **[docs/SECURITY_ANALYSIS.md](docs/SECURITY_ANALYSIS.md)** - Detailed security review
- **[docs/README.md](docs/README.md)** - Complete setup guide
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Deploy to Render
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Development workflow
- **[docs/WORKFLOW.md](docs/WORKFLOW.md)** - PR workflow guide

## 🔑 Features

- 💳 Credit card balance & utilization tracking
- 📊 Transaction history & spending analysis  
- 📈 Credit report integration (Experian)
- 🌐 Web dashboard with visualizations
- 📱 Responsive mobile-friendly UI
- ⚙️ Setup wizard for initial Plaid configuration
- 🏥 Health check endpoints for deployment monitoring

## ⚙️ Tech Stack

- **Python 3.11+**
- **Flask** - Web framework
- **Plaid API** - Financial data
- **Experian API** - Credit reports
- **Gunicorn** - Production server
- **pytest** - Testing framework

## 🧪 Testing

### Run Tests

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_plaid_integration.py

# Run tests matching pattern
pytest -k "test_plaid"
```

### View Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open in browser
start htmlcov/index.html
```

### Test Structure

```
tests/
├── conftest.py                  # Pytest configuration & fixtures
├── test_plaid_integration.py    # Plaid API tests (mocked)
├── test_experian_integration.py # Experian API tests (mocked)
└── test_app.py                  # Flask app tests
```

**Coverage Goal:** 70%+ for core business logic

## 🛠️ Development

### Available Endpoints

**Web Dashboard:**
- `GET /` - Main dashboard (shows setup instructions if credentials not configured)
- `GET /health` - Health check endpoint (for deployment monitoring)
- `GET /config-status` - Check configuration status

**API Endpoints:**
- `GET /api/data` - Full credit data (transactions, cards, balances)
- `GET /api/transactions` - Transactions only

### Setup on First Run

When you first run the app, if `PLAID_ACCESS_TOKEN` is not configured:
1. The dashboard displays an interactive setup page
2. Guides you through getting Plaid credentials
3. Instructions for running `scripts/setup_plaid_token.py`
4. Easy steps to configure environment variables on Render

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and commit
git commit -m "feat: your feature"

# Push and create PR
git push -u origin feature/your-feature
gh pr create --base main
```

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for full workflow.

## 🔐 Security & Compliance

This application handles sensitive financial data and implements industry-standard security practices:

### Data Protection
- **Encryption in Transit:** All API calls use HTTPS/TLS 1.3
- **Encryption at Rest:** Sensitive credentials encrypted in database
- **Password Security:** Passwords hashed with bcrypt (12+ rounds)
- **Token Management:** Short-lived access tokens with refresh rotation

### Privacy & Compliance
- **GDPR Compliant:** User data export and deletion endpoints
- **CCPA Ready:** Privacy controls and audit logging
- **Audit Logging:** All sensitive operations logged with timestamps and user context
- **Data Isolation:** Per-user data access — users can only view their own data

### Best Practices
- **Input Validation:** All user input validated and sanitized
- **Rate Limiting:** Auth endpoints protected against brute force attacks
- **Error Handling:** Generic error messages (implementation details never exposed)
- **Third-Party Security:** Vendors (Plaid, Experian) vetted for SOC 2 compliance

### Responsible Disclosure

Found a security vulnerability? Please email security@example.com with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We'll respond within 24 hours and credit you in our security notes.

See [SECURITY.md](SECURITY.md) for detailed security information and deployment checklist.

## 🚢 Deployment

Deploy to Render with one click:
1. Connect GitHub repository
2. Render auto-detects `config/render.yaml`
3. Set environment variables
4. Deploy!

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for details.

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🔗 Links

- [GitHub Repository](https://github.com/odanree/credit-history-app)
- [Live Demo](https://credit-history-app.onrender.com) (if deployed)
- [Plaid Docs](https://plaid.com/docs/)
- [Experian Developer Portal](https://developer.experian.com/)
