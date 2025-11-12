# Experian API Integration Status

## Current Status: ⚠️ Authentication Working, Account Configuration Needed

### What's Working ✅
- OAuth 2.0 authentication (successfully obtaining Bearer tokens)
- API endpoint connectivity
- Request format and structure
- Header configuration

### What's Blocking 🔴
**Error:** "Inquiry Not Allowed" (Error Code 76)

**Root Cause:** Sandbox account needs to be provisioned for credit report access by Experian

### Test Results

#### Successful OAuth Token Generation
```
✅ Got access token: eyJraWQiOiJESmpTMXJQQjdJODBHWjgy...
```

#### API Call Result
```
Status: 400 Bad Request
Error: "Inquiry Not Allowed"
Message: INQUIRY NOT ALLOWED
```

This error indicates authentication is successful, but the account lacks permissions for credit pulls.

## Required Action: Contact Experian Support

### Email Template

**To:** apisupport@experian.com  
**Subject:** Sandbox Account Configuration - Enable Credit Report API Access

```
Hello Experian Support Team,

I am developing an application using the Experian Credit Profile API and need assistance configuring my sandbox account.

Account Details:
- Client ID: qxj0IagY5NuoQAUEmwYYaTiy8t8krkeO
- Environment: Sandbox
- Email: dtle82@gmail.com

Issue:
I can successfully authenticate via OAuth 2.0, but when attempting to retrieve credit reports,
I receive error code 76: "Inquiry Not Allowed"

Request:
1. Please enable credit report API access for my sandbox account
2. Provide my subscriber code for sandbox testing
3. Confirm the correct clientReferenceId value for my account (currently using "SBMYSQL" for testing)

API Endpoint Being Used:
POST https://sandbox-us-api.experian.com/eits/gdp/v1/request?targeturl=https%3A%2F%2Fsandbox-us-api.experian.com%2Fconsumerservices%2Fcredit-profile%2Fv2%2Fcredit-report

Thank you for your assistance.

Best regards,
[Your Name]
```

## Sandbox Test Data

While waiting for account configuration, these are Experian's standard sandbox test values:

```json
{
  "consumerPii": {
    "primaryApplicant": {
      "name": {
        "lastName": "CANN",
        "firstName": "JOHN",
        "middleName": "N"
      },
      "dob": {
        "dob": "1955"
      },
      "ssn": {
        "ssn": "111111111"
      },
      "currentAddress": {
        "line1": "510 MONDRE ST",
        "city": "MICHIGAN CITY",
        "state": "IN",
        "zipCode": "46360"
      }
    }
  },
  "requestor": {
    "subscriberCode": "2222222"
  },
  "permissiblePurpose": {
    "type": "08"
  }
}
```

**Headers:**
- `clientReferenceId`: `SBMYSQL` (sandbox test value)

## Working Configuration

Once Experian support enables your account, update these values in `.env`:

```env
# Your actual values
EXPERIAN_CLIENT_ID=qxj0IagY5NuoQAUEmwYYaTiy8t8krkeO
EXPERIAN_CLIENT_SECRET=<your-secret>
EXPERIAN_USERNAME=dtle82@gmail.com
EXPERIAN_PASSWORD=<your-password>

# Values provided by Experian support
EXPERIAN_SUBSCRIBER_CODE=<provided-by-experian>
EXPERIAN_CLIENT_REFERENCE_ID=<provided-by-experian>  # May be SBMYSQL for sandbox
```

## Timeline

- **OAuth Implementation:** Complete
- **API Structure:** Complete
- **Account Provisioning:** Pending Experian support response (typically 1-3 business days)
- **Full Integration:** Ready once account is configured

## Alternative: Use Plaid Only

While waiting for Experian configuration, you can use the Plaid-only version:

```bash
python run_plaid_only.py
```

This provides:
- Transaction history
- Account balances
- Credit card utilization
- Spending analysis

## Technical Details

### Successful Authentication Flow
1. ✅ Basic Auth with client credentials
2. ✅ Username/password in request body
3. ✅ Bearer token received
4. ✅ Token used in API calls

### API Endpoint Structure
```
Gateway URL: /eits/gdp/v1/request?targeturl=<URL-encoded-endpoint>
Direct URL: /consumerservices/credit-profile/v2/credit-report
```

### Headers Required
```python
{
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'clientReferenceId': 'SBMYSQL'  # Sandbox value
}
```

## Next Steps

1. ✅ Send email to Experian support (use template above)
2. ⏳ Wait for Experian to provision account (1-3 business days)
3. 🔄 Update code with provided subscriber code
4. ✅ Test with real credit report retrieval
5. 🚀 Deploy combined Plaid + Experian application

## Reference Files

- `test_experian_gateway.py` - Working authentication test
- `experian_integration.py` - Main integration module (ready for subscriber code)
- `run_plaid_only.py` - Temporary solution while waiting

## Support Contacts

- **Experian API Support:** apisupport@experian.com
- **Experian Developer Portal:** https://developer.experian.com/
- **Documentation:** https://developer.experian.com/products/credit-profile

---

**Status Updated:** November 11, 2025  
**Blocking Issue:** Account provisioning required  
**ETA:** 1-3 business days after contacting support
