"""
Test Experian API connectivity with different authentication methods
"""
import os
import sys
import requests
import base64
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
client_id = os.getenv('EXPERIAN_CLIENT_ID')
client_secret = os.getenv('EXPERIAN_CLIENT_SECRET')

print("Testing Experian API Authentication Methods\n")
print(f"Client ID: {client_id[:8]}...")
print(f"Using sandbox environment\n")

# Method 1: Direct API call with headers (some Experian products use this)
print("=" * 60)
print("Method 1: Direct API Key in Headers")
print("=" * 60)

headers = {
    'Client-Id': client_id,
    'Client-Secret': client_secret,
    'Content-Type': 'application/json'
}

# Try a simple API endpoint
test_url = "https://sandbox-us-api.experian.com/consumerservices/credit-profile/v2/credit-report"

consumer_data = {
    'consumerPii': {
        'primaryApplicant': {
            'name': {
                'firstName': os.getenv('CONSUMER_FIRST_NAME', 'John'),
                'lastName': os.getenv('CONSUMER_LAST_NAME', 'Doe')
            },
            'ssn': os.getenv('CONSUMER_SSN', '666112222'),
            'dob': {
                'dob': os.getenv('CONSUMER_DOB', '1980-01-01')
            },
            'currentAddress': {
                'line1': os.getenv('CONSUMER_ADDRESS_LINE1', '10655 BIRCH ST'),
                'city': os.getenv('CONSUMER_CITY', 'Scranton'),
                'state': os.getenv('CONSUMER_STATE', 'PA'),
                'zipCode': os.getenv('CONSUMER_ZIP', '18508')
            }
        }
    },
    'requestor': {
        'subscriberCode': client_id
    },
    'permissiblePurpose': {
        'type': 'OwnCredit'
    }
}

try:
    response = requests.post(test_url, headers=headers, json=consumer_data, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Method 2: OAuth with different payload structure
print("\n" + "=" * 60)
print("Method 2: OAuth Token Request - Structure A")
print("=" * 60)

auth_url = "https://sandbox-us-api.experian.com/oauth2/v1/token"
payload = {
    'client_id': client_id,
    'client_secret': client_secret,
    'grant_type': 'client_credentials'
}

try:
    response = requests.post(auth_url, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Method 3: Form-encoded
print("\n" + "=" * 60)
print("Method 3: OAuth Token Request - Form Encoded")
print("=" * 60)

headers_form = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

data_form = f"client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"

try:
    response = requests.post(auth_url, headers=headers_form, data=data_form, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("Done")
print("=" * 60)
