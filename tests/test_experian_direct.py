"""
Test Experian API with direct endpoint (no gateway)
"""
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# Get OAuth token first
client_id = os.getenv('EXPERIAN_CLIENT_ID')
client_secret = os.getenv('EXPERIAN_CLIENT_SECRET')
username = os.getenv('EXPERIAN_USERNAME')
password = os.getenv('EXPERIAN_PASSWORD')

auth_url = "https://sandbox-us-api.experian.com/oauth2/v1/token"

# Basic Auth with client credentials
credentials = f"{client_id}:{client_secret}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'Basic {encoded_credentials}'
}

payload = {
    'username': username,
    'password': password,
    'client_id': client_id,
    'client_secret': client_secret
}

print("Getting OAuth token...")
response = requests.post(auth_url, headers=headers, json=payload)
if response.status_code == 200:
    token_data = response.json()
    access_token = token_data['access_token']
    print(f"✅ Got access token: {access_token[:50]}...\n")
else:
    print(f"❌ Failed to get token: {response.status_code}")
    print(response.text)
    exit(1)

# Now try direct API endpoint (without gateway)
print("Testing DIRECT endpoint (no gateway)...")
api_url = "https://sandbox-us-api.experian.com/consumerservices/credit-profile/v2/credit-report"

# Proper request payload with required fields
request_payload = {
    "consumerPii": {
        "primaryApplicant": {
            "name": {
                "lastName": "DOE",
                "firstName": "JOHN"
            },
            "dob": {
                "dob": "1980-01-01"
            },
            "ssn": {
                "ssn": "666601111"
            },
            "currentAddress": {
                "line1": "10655 BIRCH ST",
                "city": "SCRANTON",
                "state": "PA",
                "zipCode": "18508"
            }
        }
    },
    "requestor": {
        "subscriberCode": client_id  # This is likely the companyId they want in header
    },
    "permissiblePurpose": {
        "type": "3F",
        "terms": "Y"
    }
}

print(f"Testing: {api_url}\n")

# Test with client_id
api_headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'companyId': client_id
}

print(f"Test 1: companyId = client_id ({client_id[:20]}...)")
print(f"Headers sent: {list(api_headers.keys())}")
response = requests.post(api_url, headers=api_headers, json=request_payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}\n")

# Test with username as companyId
api_headers['companyId'] = username
print(f"Test 2: companyId = username ({username})")
response = requests.post(api_url, headers=api_headers, json=request_payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}\n")

# Test WITHOUT companyId to see what headers they see
api_headers_no_company = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
print(f"Test 3: NO companyId header")
print(f"Headers sent: {list(api_headers_no_company.keys())}")
response = requests.post(api_url, headers=api_headers_no_company, json=request_payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")
