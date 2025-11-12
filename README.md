# Credit History Application

A comprehensive credit monitoring application integrating Plaid (transaction data) and Experian (credit reports).

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r config/requirements.txt

# Configure environment
cp config/.env.example .env
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
│   │   └── dashboard.html
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

## ⚙️ Tech Stack

- **Python 3.11+**
- **Flask** - Web framework
- **Plaid API** - Financial data
- **Experian API** - Credit reports
- **Gunicorn** - Production server

## 🛠️ Development

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
