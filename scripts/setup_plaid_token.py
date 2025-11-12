"""
Get Plaid Access Token for Sandbox Testing
This script helps you complete the Plaid Link flow to get an access token
"""
import os
import sys
from dotenv import load_dotenv
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

# Initialize Plaid client
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID'),
        'secret': os.getenv('PLAID_SECRET'),
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

print("🔐 Plaid Sandbox Access Token Generator")
print("=" * 60)

try:
    # Step 1: Create a sandbox public token
    print("\n1️⃣  Creating sandbox public token...")
    
    request = SandboxPublicTokenCreateRequest(
        institution_id='ins_109508',  # Chase (sandbox test bank)
        initial_products=[Products('transactions'), Products('auth')]
    )
    
    public_token_response = client.sandbox_public_token_create(request)
    public_token = public_token_response['public_token']
    
    print(f"✅ Public token created: {public_token[:20]}...")
    
    # Step 2: Exchange public token for access token
    print("\n2️⃣  Exchanging for access token...")
    
    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = client.item_public_token_exchange(exchange_request)
    
    access_token = exchange_response['access_token']
    item_id = exchange_response['item_id']
    
    print(f"✅ Access token obtained!")
    print(f"   Item ID: {item_id}")
    
    print("\n" + "=" * 60)
    print("🎉 SUCCESS! Your Plaid access token:")
    print("=" * 60)
    print(f"\n{access_token}\n")
    
    print("📝 Add this to your .env file:")
    print("=" * 60)
    print(f"PLAID_ACCESS_TOKEN={access_token}")
    print("\n")
    
    # Try to update .env file
    print("Updating .env file automatically...")
    
    env_path = '.env'
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    with open(env_path, 'w') as f:
        for line in lines:
            if line.startswith('PLAID_ACCESS_TOKEN='):
                f.write(f'PLAID_ACCESS_TOKEN={access_token}\n')
            else:
                f.write(line)
    
    print("✅ .env file updated!")
    print("\n🚀 You can now run: python run_plaid_only.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nIf you see authentication errors, check your Plaid credentials in .env")
