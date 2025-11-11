# GitHub Copilot Instructions for Credit History Application

## Project Overview

This is a Python application that integrates with **Plaid API** (for financial transaction data) and **Experian Connect API** (for credit bureau reports) to provide a comprehensive credit history profile similar to services like Empower or Credit Karma.

## Architecture

### Core Modules
- `plaid_integration.py` - Handles Plaid API interactions for transactions and account balances
- `experian_integration.py` - Handles Experian API interactions for credit reports and scores
- `main.py` - Combines both data sources into unified credit profile

### Key Technologies
- **Python 3.11+**
- **Plaid Python SDK** - Financial data aggregation
- **Requests** - HTTP client for Experian API
- **python-dotenv** - Environment variable management
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

### Example:
```python
try:
    response = self.client.get_transactions(request)
    return response.to_dict()
except plaid.ApiException as e:
    print(f"Error fetching transactions: {e}")
    raise
```

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

## Contact & Support

For questions about:
- Plaid API: https://support.plaid.com/
- Experian API: developer@experian.com
- Code issues: Check README.md troubleshooting section
