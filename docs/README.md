# Credit History Application

A Python application that combines **Plaid** (for transaction data) and **Experian Connect** (for credit reports) to provide a complete credit history profile, similar to services like Empower.

## Features

### 📊 Complete Credit Profile
- **Credit Score** - Get your current credit score from Experian
- **Credit Report** - Full credit report with all accounts and payment history
- **Transaction History** - Real-time credit card transactions from Plaid
- **Account Balances** - Current balances and credit limits
- **Credit Utilization** - Automatic calculation across all cards
- **Recommendations** - Actionable insights to improve your credit

### 🔗 Dual API Integration

**Plaid API** - Financial data aggregation
- Transaction history (90+ days)
- Account balances
- Credit card information
- Spending analytics

**Experian Connect API** - Credit bureau data
- Credit scores (VantageScore/FICO)
- Credit report data
- Payment history
- Account details
- Hard inquiries

## Setup Instructions

### 1. Get API Credentials

#### Plaid (Free Sandbox)
1. Sign up at https://dashboard.plaid.com/signup
2. Create a new app
3. Get your `client_id` and `secret`
4. Default environment: `sandbox` (free for testing)

#### Experian Connect
1. Sign up at https://developer.experian.com/
2. Apply for API access (may require business verification)
3. Get your `client_id` and `client_secret`
4. Use `sandbox` environment for testing

### 2. Install Dependencies

```powershell
# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```powershell
# Copy the example file
Copy-Item .env.example .env

# Edit .env with your credentials
notepad .env
```

Update `.env` with your API credentials:
```env
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
EXPERIAN_CLIENT_ID=your_experian_client_id
EXPERIAN_CLIENT_SECRET=your_experian_client_secret
```

### 4. Get Plaid Access Token

Plaid requires you to complete a "Link flow" to connect accounts. Two options:

**Option A: Use Plaid Quickstart** (Recommended)
```powershell
# Clone Plaid quickstart
git clone https://github.com/plaid/quickstart.git
cd quickstart
# Follow their setup instructions to get an access_token
```

**Option B: Use Sandbox Test Credentials**
The sandbox environment allows test credentials without real bank connections.
Set `PLAID_ACCESS_TOKEN` to a test token from Plaid docs.

## Usage

### Run the Main Application

```powershell
python main.py
```

This will:
1. Fetch transaction data from Plaid
2. Fetch credit report from Experian
3. Combine data into unified profile
4. Display comprehensive summary
5. Optionally export to JSON

### Use Individual Modules

**Plaid Only (Transactions):**
```powershell
python plaid_integration.py
```

**Experian Only (Credit Report):**
```powershell
python experian_integration.py
```

## Code Examples

### Get Complete Credit Profile

```python
from main import CreditHistoryApp

app = CreditHistoryApp()

profile = app.get_complete_credit_profile(
    plaid_access_token="access-sandbox-xxx",
    consumer_info={
        'firstName': 'John',
        'lastName': 'Doe',
        'ssn': '123456789',
        'dob': '1980-01-01',
        'address': {
            'line1': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'zip': '10001'
        }
    },
    transaction_days=90
)

# Print summary
app.print_summary(profile)

# Export to JSON
app.export_to_json(profile, 'my_credit_profile.json')
```

### Get Just Credit Score

```python
from experian_integration import ExperianClient

experian = ExperianClient(
    client_id='your_id',
    client_secret='your_secret'
)

score = experian.get_credit_score(consumer_info)
print(f"Credit Score: {score['score']}")
```

### Get Just Transactions

```python
from plaid_integration import PlaidClient
from datetime import datetime, timedelta

plaid = PlaidClient(
    client_id='your_id',
    secret='your_secret'
)

transactions = plaid.get_transactions(
    access_token='your_token',
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

for txn in transactions['transactions']:
    print(f"{txn['date']}: {txn['name']} - ${txn['amount']}")
```

## Output Example

```
📊 CREDIT SCORE: 720
   Rating: Good

💳 CREDIT CARDS:
   Total Cards: 3
   Total Balance: $2,450.00
   Total Limit: $15,000.00
   Utilization: 16.3%
   Monthly Spending: $1,234.56
   Recent Transactions: 45

🏥 CREDIT HEALTH:
   Open Accounts: 8
   Delinquent Accounts: 0
   Hard Inquiries: 2
   Public Records: 0

💡 RECOMMENDATIONS:
   🟢 [LOW] Great credit score! You qualify for the best rates.
   🟡 [MEDIUM] Credit utilization is 16.3%. Keeping it below 10% could improve your score.
```

## API Costs

### Plaid
- **Sandbox:** Free (unlimited)
- **Development:** Free (100 items)
- **Production:** ~$0.30-2.50 per user/month depending on products

### Experian
- **Sandbox:** Free (limited queries)
- **Production:** Contact sales for pricing
- Typically pay-per-query model

## Security Best Practices

1. **Never commit `.env` file** - It's in `.gitignore`
2. **Use environment variables** for all credentials
3. **Rotate API keys** regularly
4. **Use HTTPS only** in production
5. **Encrypt sensitive data** at rest
6. **Follow PCI/SOC2** compliance for production

## Data Privacy

- **Consumer consent required** for all credit data
- **Permissible purpose** must be documented (Experian)
- **FCRA compliance** required for credit reporting
- **Data retention policies** - delete data when no longer needed

## Troubleshooting

### Plaid Errors

**"Invalid access token"**
- Access token expired or invalid
- Generate new token via Link flow

**"Product not enabled"**
- Enable `transactions` and `auth` products in Plaid dashboard

### Experian Errors

**"Authentication failed"**
- Check client_id and client_secret
- Ensure credentials are for correct environment (sandbox/production)

**"Consumer not found"**
- Verify SSN, DOB, and address are correct
- In sandbox, use test SSNs from Experian docs

## Next Steps

1. **Build a Web UI** - Add Flask/FastAPI frontend
2. **Add More Bureaus** - Integrate TransUnion/Equifax
3. **Credit Monitoring** - Set up automated alerts
4. **Score Simulation** - Show impact of actions on score
5. **Financial Planning** - Add budgeting features

## Resources

- [Plaid Documentation](https://plaid.com/docs/)
- [Experian API Docs](https://developer.experian.com/docs)
- [Credit Score Ranges](https://www.experian.com/blogs/ask-experian/credit-education/score-basics/what-is-a-good-credit-score/)
- [FCRA Compliance](https://www.ftc.gov/legal-library/browse/statutes/fair-credit-reporting-act)

## License

MIT License - Use at your own risk. Ensure compliance with all applicable laws and regulations.

## Support

For issues:
- Plaid: support@plaid.com
- Experian: developer@experian.com
