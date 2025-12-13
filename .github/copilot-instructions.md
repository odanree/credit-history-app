# GitHub Copilot Instructions for Credit History Application

## Project Overview

This is a Python application that integrates with **Plaid API** (for financial transaction data) and **Experian Connect API** (for credit bureau reports) to provide a comprehensive credit history profile similar to services like Empower or Credit Karma.

## Architecture

### Application Versions
The project provides two different Flask application implementations:

#### `src/app.py` - Traditional Database Architecture
- Stores customer data in database
- Caches transactions for fast performance (~5ms response)
- Requires PostgreSQL for production
- Best for: Complex analytics, historical trends, mature products
- Trade-off: More compliance overhead (GDPR data management)

#### `src/app_stateless.py` - Stateless Architecture (Recommended)
- Zero customer data storage
- Access tokens encrypted in session cookies (httpOnly)
- Fresh data fetched from Plaid on every request (~200-500ms)
- No database required
- Best for: MVP, low liability, GDPR compliance
- Trade-off: Slightly slower, depends on Plaid availability

### Choosing Your Architecture

**Use Stateless if:**
- Building MVP or proof of concept
- Want minimal compliance burden
- Don't need historical data beyond 90 days
- Prefer zero data breach risk
- Can accept ~200-500ms response time

**Use Traditional if:**
- Offering advanced analytics
- Need historical trends (6+ months)
- Want <10ms response times
- Have data engineering resources
- Planning to scale significantly

**Use Hybrid (Recommended for Scale):**
- Add Redis cache (7-day TTL) to stateless
- Best of both: Fast + simple + GDPR-friendly
- See STATELESS_ARCHITECTURE.md, Option 4

### Core Modules
- `plaid_integration.py` - Handles Plaid API interactions for transactions and account balances
- `experian_integration.py` - Handles Experian API interactions for credit reports and scores
- `main.py` - Combines both data sources into unified credit profile

### Key Technologies
- **Python 3.11+**
- **Flask** - Web framework
- **Plaid Python SDK** - Financial data aggregation
- **Requests** - HTTP client for Experian API
- **python-dotenv** - Environment variable management
- **Flask-Session** - Secure session management (stateless app)
- **cryptography** - Token encryption (stateless app)
- **pandas** - Data processing (optional)

## Code Style & Conventions

### General Guidelines
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Include comprehensive docstrings for all classes and methods
- Use descriptive variable names (e.g., `credit_score` not `cs`)
- Keep functions focused and under 50 lines when possible

### Error Handling
- Always wrap API calls in try-except blocks
- Provide meaningful error messages to users
- Log errors with context (e.g., which API, what operation)
- Never expose API keys or sensitive data in error messages

### Flask Web App Error Handling
- Missing credentials show setup page (not error message)
- API endpoints return 503 when credentials missing (not 500)
- Health check endpoints (`/health`, `/config-status`) for monitoring
- Graceful degradation: show helpful instructions instead of breaking
- Use HTTP 503 (Service Unavailable) for missing config
- Use HTTP 500 only for unexpected application errors

### Example:
```python
try:
    response = self.client.get_transactions(request)
    return response.to_dict()
except plaid.ApiException as e:
    print(f"Error fetching transactions: {e}")
    raise
```

## Stateless Architecture (app_stateless.py)

### Session Management
- **Token Storage:** Plaid access token encrypted in httpOnly session cookie
- **Encryption:** Use Fernet (cryptography library) with TOKEN_ENCRYPTION_KEY
- **Session Lifetime:** Default 24 hours, configurable per deployment
- **Cookie Security:**
  ```python
  SESSION_COOKIE_HTTPONLY = True   # Prevent JavaScript access
  SESSION_COOKIE_SECURE = True      # HTTPS only (production)
  SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
  ```

### Data Flow (Stateless Pattern)
1. **User Setup:** Paste Plaid access token on setup page
2. **Token Encryption:** Token encrypted and stored in session cookie
3. **Request Time:** Retrieve encrypted token from session, decrypt it
4. **Fresh Data:** Call Plaid API to fetch current data (not stored)
5. **Response:** Return data directly to frontend, discard after response
6. **Zero Storage:** No customer financial data in database

### Implementation Pattern
```python
class StatelessPlaidClient:
    """Fetch fresh data on-demand, never store it"""
    
    def get_token_from_session(self) -> str:
        """Decrypt access token from encrypted session"""
        encrypted_token = session['plaid_token']
        return token_encryption.decrypt(encrypted_token)
    
    def store_token_in_session(self, access_token: str):
        """Encrypt and store access token in session"""
        encrypted = token_encryption.encrypt(access_token)
        session['plaid_token'] = encrypted
        session.permanent = True
        session.modified = True
    
    def get_dashboard_data(self) -> dict:
        """Fetch fresh data from Plaid (NOT stored in database)"""
        access_token = self.get_token_from_session()
        credit_data = plaid_client.get_credit_card_data(access_token)
        # Return directly, don't store
        return credit_data
```

### GDPR/CCPA Compliance (Stateless)
- **Data Export:** "We don't store customer financial data"
- **Data Deletion:** Clear session cookie and user record
- **Right to Access:** User can export any time (fresh from Plaid)
- **Data Retention:** Session cookie expires per configuration

### When to Use Stateless
✅ MVP, proof of concept
✅ Low-traffic applications
✅ GDPR/CCPA sensitive projects
✅ Minimal compliance requirements
✅ Can tolerate 200-500ms latency
❌ Don't use for: Complex analytics, 6+ months history, <10ms requirements

## API Integration Best Practices

### Plaid API
- Use the official `plaid-python` SDK
- Handle pagination for transactions (use offset parameter)
- Check `total_transactions` vs retrieved count
- Always specify date ranges for transaction queries
- Use sandbox environment for development

### Experian API
- Implement OAuth 2.0 token refresh logic
- Cache access tokens until expiry
- Include all required consumer PII fields
- Use permissible purpose codes correctly (`OwnCredit` for consumer access)
- Handle rate limits gracefully

## Security Requirements

### Credentials Management
- NEVER hardcode API keys or secrets
- Always use environment variables via `.env` file
- Add `.env` to `.gitignore` immediately
- Use `.env.example` as template without real values

### Data Privacy
- Minimize storage of sensitive data (SSN, account numbers)
- Mask SSN in logs and outputs (show last 4 digits only)
- Implement data retention policies
- Follow FCRA compliance for credit data
- Require explicit user consent before data collection

### Example:
```python
# Good - masked SSN
print(f"SSN: ***-**-{ssn[-4:]}")

# Bad - exposing full SSN
print(f"SSN: {ssn}")
```

## Feature Development Guidelines

### When Adding New Features

1. **Data Fetching**
   - Add methods to appropriate integration module
   - Include error handling and validation
   - Return consistent data structures (dicts/lists)
   - Document expected response format

2. **Data Processing**
   - Create helper methods in respective classes
   - Keep business logic separate from API calls
   - Add type hints and docstrings

3. **User-Facing Features**
   - Update `main.py` with new functionality
   - Add to combined summary if relevant
   - Update recommendations logic if applicable
   - Ensure backward compatibility

### Testing
- Test with sandbox/test credentials first
- Verify error handling with invalid inputs
- Check edge cases (no transactions, low score, etc.)
- Test with both Plaid and Experian data unavailable

## Common Patterns

### Fetching API Data
```python
def get_data(self, params: Dict) -> Dict:
    """
    Fetch data from API
    
    Args:
        params: Request parameters
        
    Returns:
        Dict containing response data
    """
    try:
        response = self.client.api_call(params)
        return response.to_dict()
    except Exception as e:
        print(f"Error fetching data: {e}")
        raise
```

### Combining Data Sources
```python
def combine_data(self, plaid_data: Dict, experian_data: Dict) -> Dict:
    """Merge data from multiple sources"""
    combined = {}
    
    # Check for errors in either source
    if 'error' not in plaid_data:
        combined['transactions'] = plaid_data.get('transactions', [])
    
    if 'error' not in experian_data:
        combined['credit_score'] = experian_data.get('credit_score')
    
    return combined
```

### Generating Recommendations
```python
def generate_recommendation(self, metric: float, threshold: float) -> dict:
    """Generate recommendation based on metric"""
    if metric > threshold:
        return {
            'priority': 'high',
            'category': 'category_name',
            'message': 'User-friendly message with actionable advice'
        }
```

## Environment Variables

### Required Variables
```env
PLAID_CLIENT_ID=        # From Plaid dashboard
PLAID_SECRET=           # From Plaid dashboard
PLAID_ENV=sandbox       # sandbox, development, or production
PLAID_ACCESS_TOKEN=     # After Link flow completion

EXPERIAN_CLIENT_ID=     # From Experian developer portal
EXPERIAN_CLIENT_SECRET= # From Experian developer portal
EXPERIAN_ENV=sandbox    # sandbox or production
```

### Consumer Data (Testing)
```env
CONSUMER_FIRST_NAME=
CONSUMER_LAST_NAME=
CONSUMER_SSN=           # Use sandbox test SSNs
CONSUMER_DOB=           # Format: YYYY-MM-DD
CONSUMER_ADDRESS_LINE1=
CONSUMER_CITY=
CONSUMER_STATE=         # Two-letter code
CONSUMER_ZIP=
```

## File Organization

### When Creating New Files
- Keep integrations in `*_integration.py` files
- Use `utils.py` for shared helper functions
- Create `models.py` for data classes if needed
- Add tests in `tests/` directory

### Import Order
1. Standard library imports
2. Third-party imports
3. Local application imports

```python
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from plaid.api import plaid_api

from utils import format_currency
```

## Documentation

### Docstring Format
Use Google-style docstrings:

```python
def function_name(param1: str, param2: int = 0) -> Dict:
    """
    Brief description of function
    
    Longer description if needed, explaining what the function does,
    any important considerations, or usage examples.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)
        
    Returns:
        Dict containing:
            - key1: Description of key1
            - key2: Description of key2
            
    Raises:
        ValueError: If param1 is empty
        APIException: If API call fails
    """
```

### README Updates
When adding new features:
- Update feature list
- Add usage examples
- Update API comparison table if relevant
- Add troubleshooting tips

### Documentation Updates for Major Changes
**IMPORTANT:** Always update root-level documentation when making significant changes:

1. **Update README.md** when:
   - Adding new modules or files
   - Changing API integrations or endpoints
   - Modifying setup/installation steps
   - Adding new dependencies
   - Changing environment variables
   - Adding new features users will interact with
   - Modifying output formats or data structures

2. **Update .github/copilot-instructions.md** when:
   - Changing project architecture or file structure
   - Adding new design patterns or conventions
   - Implementing new security measures
   - Adding new APIs or external services
   - Changing error handling strategies
   - Modifying data flow between modules
   - Adding new compliance requirements

3. **What to Document:**
   - **Architecture changes**: New modules, refactored components, data flow changes
   - **API changes**: New endpoints, changed request/response formats, authentication updates
   - **Breaking changes**: Changes that require users to update their code or configuration
   - **New patterns**: Reusable code patterns that should be followed project-wide
   - **Security updates**: New security measures, credential handling changes
   - **Configuration changes**: New environment variables, settings, or config files

4. **Documentation Standards:**
   - Keep README.md user-focused (how to use)
   - Keep copilot-instructions.md developer-focused (how to build)
   - Include code examples for new features
   - Add troubleshooting for common issues
   - Update table of contents if applicable
   - Mark deprecated features clearly
   - Include migration guides for breaking changes

## Debugging Tips

### Common Issues

**Plaid "Invalid Access Token"**
- Token may have expired
- Regenerate via Link flow
- Check environment (sandbox vs production tokens)

**Experian "Consumer Not Found"**
- Verify all PII fields are correct
- Use sandbox test data from Experian docs
- Check date format (YYYY-MM-DD)

**Rate Limiting**
- Implement exponential backoff
- Cache responses when appropriate
- Use batch endpoints when available

## Performance Considerations

- Cache Experian access tokens (valid for 1 hour)
- Limit transaction queries to necessary date ranges
- Use account_ids to filter specific accounts
- Consider async/await for multiple API calls
- Paginate large result sets

## Compliance & Legal

### FCRA Compliance
- Document permissible purpose for credit pulls
- Implement dispute resolution process
- Provide adverse action notices when required
- Maintain audit logs of credit access

### Data Handling
- Encrypt sensitive data at rest
- Use HTTPS for all API communications
- Implement data retention policies
- Allow users to delete their data
- Follow GDPR/CCPA requirements where applicable

## When Suggesting Code

### DO:
- Include error handling
- Add type hints and docstrings
- Follow existing code patterns
- Consider edge cases
- Suggest security best practices
- Provide usage examples

### DON'T:
- Hardcode credentials or sensitive data
- Ignore error cases
- Break existing functionality
- Suggest insecure patterns
- Remove important validation

## Useful Resources

- [Plaid API Docs](https://plaid.com/docs/)
- [Experian Developer Portal](https://developer.experian.com/)
- [FCRA Overview](https://www.ftc.gov/legal-library/browse/statutes/fair-credit-reporting-act)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## Git Commit Conventions

### Use Conventional Commits
Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for all commit messages.

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature for the user
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Changes to build system or dependencies
- `ci`: Changes to CI configuration files and scripts
- `chore`: Other changes that don't modify src or test files
- `revert`: Reverts a previous commit

**Scopes (optional):**
- `plaid`: Plaid API integration
- `experian`: Experian API integration
- `auth`: Authentication/authorization
- `api`: General API changes
- `ui`: User interface
- `config`: Configuration files
- `deps`: Dependencies

**Examples:**
```bash
feat(plaid): add support for investment accounts
fix(experian): handle expired OAuth tokens correctly
docs(readme): update API key setup instructions
refactor(main): simplify credit summary calculation
perf(plaid): cache transaction responses
test(experian): add unit tests for credit score parsing
build(deps): upgrade plaid-python to v15.0.0
chore(gitignore): add .vscode to ignored files
```

**Breaking Changes:**
Add `BREAKING CHANGE:` in the footer or use `!` after type/scope:
```bash
feat(api)!: change credit summary response format

BREAKING CHANGE: credit_summary now returns utilization as decimal instead of percentage
```

**Best Practices:**
- Use imperative mood in subject ("add" not "added" or "adds")
- Don't capitalize first letter of subject
- No period at the end of subject
- Keep subject under 50 characters
- Separate subject from body with blank line
- Wrap body at 72 characters
- Use body to explain what and why, not how

## Testing Guidelines

### Test Coverage Requirements
- **Minimum Coverage:** 70% for core business logic
- **Critical Paths:** 90%+ coverage (authentication, payment processing, data fetching)
- **New Features:** Must include tests before merging

### Testing Framework
- **pytest** - Primary testing framework
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking external dependencies
- **pytest-flask** - Flask application testing

### Test Organization

```
tests/
├── conftest.py                  # Shared fixtures and configuration
├── test_plaid_integration.py    # Plaid API client tests
├── test_experian_integration.py # Experian API client tests
└── test_app.py                  # Flask application tests
```

### Writing Tests

**1. Unit Tests (Preferred)**
- Test individual functions/methods in isolation
- Mock all external dependencies (APIs, databases, file I/O)
- Fast execution (< 1 second per test)
- No network calls or file system access

```python
@patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
def test_get_credit_card_data_success(mock_plaid_api, plaid_client):
    """Test successful credit card data retrieval"""
    # Mock the API response
    mock_response = MagicMock()
    mock_response.to_dict.return_value = {'cards': [...]}
    
    mock_plaid_api.return_value.accounts_get.return_value = mock_response
    
    result = plaid_client.get_credit_card_data('test_token')
    
    assert 'cards' in result
    assert len(result['cards']) > 0
```

**2. Mocking External APIs**
- **Always mock** Plaid and Experian API calls in tests
- Don't hit real APIs (costs money, rate limits, unreliable)
- Use `unittest.mock.patch` or `pytest-mock`
- Return realistic test data matching actual API responses

```python
# Good - mocked API call
@patch('requests.post')
def test_experian_auth(mock_post):
    mock_post.return_value.json.return_value = {'access_token': 'test_token'}
    # Test code here

# Bad - real API call
def test_experian_auth():
    response = requests.post(EXPERIAN_URL, ...)  # DON'T DO THIS
```

**3. Test Naming Conventions**
- Use descriptive names: `test_<function>_<scenario>_<expected_result>`
- Examples:
  - `test_get_credit_data_success()`
  - `test_get_credit_data_missing_token_returns_error()`
  - `test_calculate_utilization_zero_limit_returns_zero()`

**4. Test Structure (Arrange-Act-Assert)**
```python
def test_calculate_utilization():
    # Arrange - set up test data
    balance = 1000
    limit = 5000
    
    # Act - call the function
    result = calculate_utilization(balance, limit)
    
    # Assert - verify the result
    assert result == 20.0
```

**5. Testing Flask Routes**
```python
def test_dashboard_route(client):
    """Test dashboard renders successfully"""
    response = client.get('/')
    
    assert response.status_code == 200
    assert b'Credit Dashboard' in response.data
```

**6. Edge Cases to Test**
- Null/None inputs
- Empty lists/dicts
- Zero values
- Extremely large numbers
- Invalid data types
- API errors (401, 500, timeout)
- Network failures

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_plaid_integration.py

# Run tests matching pattern
pytest -k "test_plaid"

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Coverage Reporting

```bash
# Generate coverage report
pytest --cov=src --cov-report=term-missing

# Generate HTML report
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser

# View coverage for specific file
pytest --cov=src.integrations.plaid_integration --cov-report=term
```

### CI/CD Integration
- Tests run automatically on every Pull Request
- Coverage reports uploaded to Codecov
- PRs should not decrease overall coverage
- Failing tests block merge (unless overridden)

### What NOT to Test
- Third-party library internals (trust pytest, Flask, Plaid SDK work)
- Simple getters/setters without logic
- Auto-generated code
- Configuration files

### Test-Driven Development (TDD) - Recommended
1. Write failing test first
2. Write minimal code to make it pass
3. Refactor code
4. Repeat

### Common Pitfalls to Avoid
- ❌ Testing implementation instead of behavior
- ❌ Not mocking external dependencies
- ❌ Overly complex test setup
- ❌ Tests that depend on each other
- ❌ Ignoring flaky tests
- ❌ Not testing error cases
- ❌ Hard-coding test data that breaks easily

### When Adding Tests for New Features
1. **Before writing code:** Write test cases for expected behavior
2. **Mock dependencies:** External APIs, databases, file I/O
3. **Test happy path:** Normal successful execution
4. **Test error cases:** Invalid input, API failures, edge cases
5. **Check coverage:** Aim for 80%+ on new code
6. **Update CI:** Ensure tests run in GitHub Actions

### Example Test Checklist
- [ ] Tests pass locally (`pytest`)
- [ ] Coverage > 70% for new code
- [ ] All external APIs mocked
- [ ] Edge cases covered
- [ ] Error handling tested
- [ ] Tests run in CI/CD
- [ ] No flaky tests (random failures)

## Contact & Support

For questions about:
- Plaid API: https://support.plaid.com/
- Experian API: developer@experian.com
- Code issues: Check README.md troubleshooting section

