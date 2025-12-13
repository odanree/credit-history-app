# Credit History Application

[![codecov](https://codecov.io/gh/odanree/credit-history-app/branch/main/graph/badge.svg)](https://codecov.io/gh/odanree/credit-history-app)
[![Tests](https://github.com/odanree/credit-history-app/workflows/Pull%20Request%20CI/badge.svg)](https://github.com/odanree/credit-history-app/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive credit monitoring application integrating Plaid (transaction data) and Experian (credit reports).

## 🚀 Quick Start

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API credentials

# Run Flask dashboard
python -m src.app
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
│   ├── app.py              # Flask web dashboard
│   └── main.py             # Combined API client
├── scripts/                 # Utility scripts
│   ├── setup_plaid_token.py
│   └── run_plaid_only.py
├── tests/                   # Test files
│   └── test_*.py
├── config/                  # Configuration files
│   ├── requirements.txt
│   ├── .env.example
│   ├── render.yaml
│   └── Procfile
├── docs/                    # Documentation
│   ├── README.md           # Full documentation
│   ├── DEPLOYMENT.md
│   ├── CONTRIBUTING.md
│   └── WORKFLOW.md
└── .github/                 # GitHub configs
    └── workflows/
```

## 📚 Documentation

- **[Full Documentation](docs/README.md)** - Complete setup guide
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Deploy to Render
- **[Contributing](docs/CONTRIBUTING.md)** - Development workflow
- **[Git Workflow](docs/WORKFLOW.md)** - PR workflow guide

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
