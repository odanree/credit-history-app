#!/usr/bin/env python3
"""Test script for stateless app with Plaid API"""

import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptography.fernet import Fernet
from src.integrations.plaid_integration import PlaidClient

def test_encryption():
    """Test token encryption/decryption"""
    print("\n✅ TEST 1: Token Encryption/Decryption")
    print("-" * 60)
    
    encryption_key = os.getenv('TOKEN_ENCRYPTION_KEY')
    if not encryption_key:
        print("❌ TOKEN_ENCRYPTION_KEY not set in .env")
        return False
    
    cipher = Fernet(encryption_key.encode())
    
    # Original token
    original_token = "access-sandbox-12345"
    
    # Encrypt
    encrypted = cipher.encrypt(original_token.encode())
    print(f"✓ Original token: {original_token}")
    print(f"✓ Encrypted: {encrypted.hex()[:50]}...")
    
    # Decrypt
    decrypted = cipher.decrypt(encrypted).decode()
    print(f"✓ Decrypted: {decrypted}")
    
    # Verify
    if decrypted == original_token:
        print("✓ Encryption/decryption works correctly!")
        return True
    else:
        print("❌ Decrypted token doesn't match original")
        return False

def test_plaid_connection():
    """Test Plaid API connection with real credentials"""
    print("\n✅ TEST 2: Plaid API Connection")
    print("-" * 60)
    
    client_id = os.getenv('PLAID_CLIENT_ID')
    secret = os.getenv('PLAID_SECRET')
    env = os.getenv('PLAID_ENV', 'sandbox')
    access_token = os.getenv('PLAID_ACCESS_TOKEN')
    
    if not all([client_id, secret, access_token]):
        print("❌ Missing Plaid credentials in .env")
        return False
    
    print(f"✓ Client ID: {client_id[:20]}...")
    print(f"✓ Environment: {env}")
    print(f"✓ Access Token: {access_token[:30]}...")
    
    try:
        client = PlaidClient(client_id, secret, env)
        print("✓ PlaidClient initialized")
        
        # Fetch data
        credit_data = client.get_credit_card_data(access_token)
        
        if 'error' in credit_data:
            print(f"❌ Plaid API error: {credit_data['error']}")
            return False
        
        # Check response structure
        cards = credit_data.get('cards', [])
        transactions = credit_data.get('transactions', [])
        accounts = credit_data.get('accounts', [])
        
        print(f"✓ Fetched {len(accounts)} accounts")
        print(f"✓ Fetched {len(cards)} credit cards")
        print(f"✓ Fetched {len(transactions)} transactions")
        
        if len(cards) > 0:
            card = cards[0]
            print(f"\nSample card:")
            print(f"  - Name: {card.get('name', 'N/A')}")
            print(f"  - Balance: ${card.get('balance', 0)}")
            print(f"  - Limit: ${card.get('limit', 0)}")
        
        if len(transactions) > 0:
            txn = transactions[0]
            print(f"\nSample transaction:")
            print(f"  - Merchant: {txn.get('name', 'N/A')}")
            print(f"  - Amount: ${txn.get('amount', 0)}")
            print(f"  - Date: {txn.get('date', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_stateless_session():
    """Test session-based token storage pattern"""
    print("\n✅ TEST 3: Stateless Session Pattern")
    print("-" * 60)
    
    encryption_key = os.getenv('TOKEN_ENCRYPTION_KEY')
    access_token = os.getenv('PLAID_ACCESS_TOKEN')
    
    if not all([encryption_key, access_token]):
        print("❌ Missing credentials")
        return False
    
    cipher = Fernet(encryption_key.encode())
    
    # Simulate session storage
    print("Simulating Flask session storage...")
    
    # Encrypt token
    encrypted_token = cipher.encrypt(access_token.encode()).hex()
    print(f"✓ Token encrypted and stored in session: {encrypted_token[:50]}...")
    
    # Simulate retrieving from session
    encrypted_from_session = bytes.fromhex(encrypted_token)
    decrypted_token = cipher.decrypt(encrypted_from_session).decode()
    
    print(f"✓ Token retrieved from session and decrypted")
    
    # Verify token works with Plaid
    client_id = os.getenv('PLAID_CLIENT_ID')
    secret = os.getenv('PLAID_SECRET')
    env = os.getenv('PLAID_ENV')
    
    try:
        client = PlaidClient(client_id, secret, env)
        data = client.get_credit_card_data(decrypted_token)
        
        if 'error' in data:
            print(f"❌ Token doesn't work: {data['error']}")
            return False
        
        print(f"✓ Decrypted token works with Plaid API")
        print(f"✓ Received fresh data (not from database)")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("STATELESS APP - LOCAL TESTING WITH PLAID API")
    print("="*60)
    
    results = {
        "Encryption/Decryption": test_encryption(),
        "Plaid Connection": test_plaid_connection(),
        "Session Pattern": test_stateless_session(),
    }
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("="*60)
    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\nStateless app is ready for use:")
        print("  1. Run: python3 -m src.app_stateless")
        print("  2. Visit: http://localhost:5001")
        print("  3. Paste your Plaid token on setup page")
        print("  4. Fresh data fetched on every request (no database)")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
