"""
Credit History Application - Plaid Only Version
Use this while troubleshooting Experian API access
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from plaid_integration import PlaidClient
import json


def main():
    """Run credit analysis with Plaid data only"""
    load_dotenv()
    
    print("Credit History Application (Plaid Only)")
    print("=" * 60)
    
    # Check for Plaid credentials
    if not os.getenv('PLAID_CLIENT_ID') or not os.getenv('PLAID_SECRET'):
        print("❌ Missing PLAID credentials in .env file")
        return
    
    plaid_access_token = os.getenv('PLAID_ACCESS_TOKEN')
    
    if not plaid_access_token:
        print("\n⚠️  No PLAID_ACCESS_TOKEN found")
        print("To get transaction data, you need to:")
        print("1. Complete the Plaid Link flow")
        print("2. Add the access_token to your .env file")
        print("\nFor now, I'll generate a link token for you:\n")
        
        try:
            plaid = PlaidClient(
                client_id=os.getenv('PLAID_CLIENT_ID'),
                secret=os.getenv('PLAID_SECRET'),
                environment=os.getenv('PLAID_ENV', 'sandbox')
            )
            
            link_token = plaid.create_link_token(user_id="user_" + datetime.now().strftime("%Y%m%d"))
            print(f"✅ Link Token Generated: {link_token['link_token']}")
            print(f"\nUse this token with Plaid Link to connect accounts.")
            print(f"Visit: https://plaid.com/docs/quickstart/ for integration guide")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return
    
    # If we have access token, fetch data
    try:
        plaid = PlaidClient(
            client_id=os.getenv('PLAID_CLIENT_ID'),
            secret=os.getenv('PLAID_SECRET'),
            environment=os.getenv('PLAID_ENV', 'sandbox')
        )
        
        print("\n📊 Fetching your financial data...")
        
        # Get credit card data
        credit_data = plaid.get_credit_card_data(plaid_access_token, days=90)
        
        print("\n" + "=" * 60)
        print("CREDIT CARD SUMMARY")
        print("=" * 60)
        
        print(f"\n💳 Total Cards: {credit_data['total_cards']}")
        print(f"💰 Total Balance: ${credit_data['total_balance']:,.2f}")
        print(f"🎯 Total Credit Limit: ${credit_data['total_limit']:,.2f}")
        
        if credit_data['total_limit'] > 0:
            utilization = (credit_data['total_balance'] / credit_data['total_limit']) * 100
            print(f"📊 Overall Utilization: {utilization:.1f}%")
            
            # Recommendation based on utilization
            if utilization > 30:
                print(f"\n⚠️  Your utilization is {utilization:.1f}%")
                print(f"   Try to keep it below 30% for better credit health")
            elif utilization > 10:
                print(f"\n✅ Your utilization is good at {utilization:.1f}%")
                print(f"   Keeping it below 10% could help improve your score")
            else:
                print(f"\n🌟 Excellent! Your utilization is only {utilization:.1f}%")
        
        print(f"\n" + "=" * 60)
        print("INDIVIDUAL CARDS")
        print("=" * 60)
        
        for card in credit_data['credit_cards']:
            print(f"\n{card['name']}")
            print(f"  Balance: ${card['current_balance']:,.2f}")
            if card.get('credit_limit'):
                print(f"  Limit: ${card['credit_limit']:,.2f}")
                available = card.get('available') or 0
                print(f"  Available: ${available:,.2f}")
                print(f"  Utilization: {card['utilization_percent']:.1f}%")
        
        print(f"\n" + "=" * 60)
        print(f"RECENT TRANSACTIONS ({len(credit_data['transactions'])} total)")
        print("=" * 60)
        
        # Show last 10 transactions
        for txn in credit_data['transactions'][:10]:
            amount = txn.get('amount', 0)
            category = txn.get('category', ['Other'])
            category_name = category[0] if category else 'Other'
            print(f"\n{txn.get('date')}: {txn.get('name')}")
            print(f"  ${amount:.2f} - {category_name}")
        
        if len(credit_data['transactions']) > 10:
            print(f"\n... and {len(credit_data['transactions']) - 10} more transactions")
        
        # Export option
        print(f"\n" + "=" * 60)
        export = input("\nExport full data to JSON? (y/n): ").lower()
        if export == 'y':
            filename = f"credit_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(credit_data, f, indent=2, default=str)
            print(f"✅ Exported to: {filename}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
