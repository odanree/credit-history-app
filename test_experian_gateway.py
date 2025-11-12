"""Test Experian API via Gateway endpoint"""
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# Get credentials
client_id = os.getenv('EXPERIAN_CLIENT_ID')
client_secret = os.getenv('EXPERIAN_CLIENT_SECRET')
username = os.getenv('EXPERIAN_USERNAME')
password = os.getenv('EXPERIAN_PASSWORD')

# OAuth endpoint
token_url = "https://sandbox-us-api.experian.com/oauth2/v1/token"

# Create Basic Auth header
credentials = f"{client_id}:{client_secret}"
basic_auth = base64.b64encode(credentials.encode()).decode()

print("Getting OAuth token...")
token_headers = {
    'Authorization': f'Basic {basic_auth}',
    'Content-Type': 'application/x-www-form-urlencoded'
}

token_data = {
    'grant_type': 'password',
    'username': username,
    'password': password
}

token_response = requests.post(token_url, headers=token_headers, data=token_data)
access_token = token_response.json()['access_token']
print(f"✅ Got access token: {access_token[:50]}...\n")

# Test GATEWAY endpoint
print("Testing GATEWAY endpoint...")
gateway_url = "https://sandbox-us-api.experian.com/eits/gdp/v1/request"

# Gateway uses clientReferenceId - for sandbox use "SBMYSQL"
gateway_headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'clientReferenceId': 'SBMYSQL'  # Sandbox test value
}

# Gateway request - targeturl should be URL-encoded in query param, not in body
# Using the format from working curl command
api_url_encoded = "https%3A%2F%2Fsandbox-us-api.experian.com%2Fconsumerservices%2Fcredit-profile%2Fv2%2Fcredit-report"
gateway_url_with_target = f"{gateway_url}?targeturl={api_url_encoded}"

# Request payload (same structure as curl)
# Request payload (same structure as curl)
gateway_payload = {
    "consumerPii": {
        "primaryApplicant": {
            "name": {
                "lastName": "CANN",
                "firstName": "JOHN",
                "middleName": "N"
            },
            "dob": {
                "dob": "1955"  # Just year for sandbox
            },
            "ssn": {
                "ssn": "111111111"  # Sandbox test SSN
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
        "subscriberCode": "2222222"  # Sandbox test subscriber code
    },
    "permissiblePurpose": {
        "type": "08"  # Credit transaction type
    },
    "resellerInfo": {
        "endUserName": "CPAPIV2TC21"
    },
    "vendorData": {
        "vendorNumber": "072",
        "vendorVersion": "V1.29"
    },
    "addOns": {
        "fraudShield": "Y"
    },
    "customOptions": {
        "optionId": ["COADEX"]
    }
}

print(f"Calling: {gateway_url_with_target}")
print(f"clientReferenceId: SBMYSQL")
print(f"Headers: {list(gateway_headers.keys())}\n")

response = requests.post(gateway_url_with_target, headers=gateway_headers, json=gateway_payload)

print(f"Status Code: {response.status_code}")
print(f"Response:\n{response.text[:1000]}")

if response.status_code == 200:
    print("\n✅ SUCCESS!")
else:
    print(f"\n❌ Error {response.status_code}")
