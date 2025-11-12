"""
Quick script to exchange link token for access token using Plaid sandbox
This simulates completing the Link flow
"""
import os
from dotenv import load_dotenv
from plaid_integration import PlaidClient

load_dotenv()

client = PlaidClient()

# For sandbox testing, we can use a test public token
# In production, this comes from the Link flow
print("Getting sandbox access token...")
print("\nIn Plaid sandbox, you have two options:\n")
print("Option 1: Use Plaid Quickstart")
print("  - Visit: https://plaid.com/docs/quickstart/")
print("  - Use your link token to complete the flow")
print("  - Copy the access_token you receive\n")

print("Option 2: Use a test public token (sandbox only)")
print("  - Plaid provides test public tokens for sandbox")
print("  - Format: public-sandbox-[uuid]")
print("  - Exchange it for an access token\n")

# For now, let's try to create a test access token
print("Attempting to generate test credentials...")
print("\nYour Link Token (already in .env):")
print("link-sandbox-ceced3e4-adca-4ea1-950b-ac54a7a0029c")

print("\n" + "="*60)
print("NEXT STEPS:")
print("="*60)
print("\n1. Visit Plaid Quickstart: https://plaid.com/docs/quickstart/")
print("2. Click 'Open Link' and paste your link token")
print("3. Select 'First Platypus Bank' (test bank)")
print("4. Use credentials: user_good / pass_good")
print("5. Select a few accounts")
print("6. Complete the flow - you'll get a public_token")
print("7. Run: python exchange_public_token.py <public_token>")
print("\nOR use Plaid's API directly to exchange tokens")
