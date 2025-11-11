"""
Plaid API Integration
Fetches transaction history, account balances, and financial data
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode


class PlaidClient:
    """Client for interacting with Plaid API"""
    
    def __init__(self, client_id: str, secret: str, environment: str = "sandbox"):
        """
        Initialize Plaid client
        
        Args:
            client_id: Your Plaid client ID
            secret: Your Plaid secret key
            environment: 'sandbox', 'development', or 'production'
        """
        env_map = {
            'sandbox': plaid.Environment.Sandbox,
            'development': plaid.Environment.Development,
            'production': plaid.Environment.Production
        }
        
        configuration = plaid.Configuration(
            host=env_map.get(environment, plaid.Environment.Sandbox),
            api_key={
                'clientId': client_id,
                'secret': secret,
            }
        )
        
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        self.client_id = client_id
    
    def create_link_token(self, user_id: str) -> Dict:
        """
        Create a Link token for Plaid Link initialization
        
        Args:
            user_id: Unique identifier for your user
            
        Returns:
            Dict containing link_token
        """
        try:
            request = LinkTokenCreateRequest(
                products=[Products("transactions"), Products("auth")],
                client_name="Credit History App",
                country_codes=[CountryCode('US')],
                language='en',
                user=LinkTokenCreateRequestUser(
                    client_user_id=user_id
                )
            )
            response = self.client.link_token_create(request)
            return response.to_dict()
        except plaid.ApiException as e:
            print(f"Error creating link token: {e}")
            raise
    
    def get_accounts(self, access_token: str) -> List[Dict]:
        """
        Get all accounts for a user
        
        Args:
            access_token: Plaid access token for the user
            
        Returns:
            List of account dictionaries
        """
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            return response.to_dict()['accounts']
        except plaid.ApiException as e:
            print(f"Error fetching accounts: {e}")
            raise
    
    def get_transactions(
        self, 
        access_token: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        account_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Get transactions for specified date range
        
        Args:
            access_token: Plaid access token
            start_date: Start date for transactions (default: 30 days ago)
            end_date: End date for transactions (default: today)
            account_ids: Optional list of specific account IDs
            
        Returns:
            Dict containing transactions and accounts
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        try:
            options = TransactionsGetRequestOptions()
            if account_ids:
                options.account_ids = account_ids
            
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date(),
                options=options
            )
            
            response = self.client.transactions_get(request)
            transactions = response.to_dict()
            
            # Handle pagination if there are more transactions
            while len(transactions['transactions']) < transactions['total_transactions']:
                options.offset = len(transactions['transactions'])
                request.options = options
                response = self.client.transactions_get(request)
                transactions['transactions'].extend(response['transactions'])
            
            return transactions
        except plaid.ApiException as e:
            print(f"Error fetching transactions: {e}")
            raise
    
    def get_credit_card_data(self, access_token: str, days: int = 90) -> Dict:
        """
        Get credit card specific data (balances, transactions, utilization)
        
        Args:
            access_token: Plaid access token
            days: Number of days of history to fetch
            
        Returns:
            Dict containing credit card summary
        """
        accounts = self.get_accounts(access_token)
        
        # Filter for credit card accounts
        credit_cards = [
            acc for acc in accounts 
            if acc.get('type') == 'credit'
        ]
        
        # Get transactions for credit cards
        start_date = datetime.now() - timedelta(days=days)
        card_ids = [card['account_id'] for card in credit_cards]
        
        transactions_data = self.get_transactions(
            access_token, 
            start_date=start_date,
            account_ids=card_ids
        )
        
        # Calculate utilization for each card
        credit_summary = []
        for card in credit_cards:
            balance = card['balances']
            utilization = 0
            if balance.get('limit') and balance['limit'] > 0:
                utilization = (balance['current'] / balance['limit']) * 100
            
            credit_summary.append({
                'name': card['name'],
                'account_id': card['account_id'],
                'current_balance': balance['current'],
                'credit_limit': balance.get('limit'),
                'available': balance.get('available'),
                'utilization_percent': round(utilization, 2),
                'last_updated': balance.get('last_updated_datetime')
            })
        
        return {
            'credit_cards': credit_summary,
            'total_cards': len(credit_cards),
            'total_balance': sum(card['current_balance'] for card in credit_summary),
            'total_limit': sum(card.get('credit_limit', 0) or 0 for card in credit_summary),
            'transactions': transactions_data['transactions']
        }


def main():
    """Example usage"""
    # Load from environment variables
    client_id = os.getenv('PLAID_CLIENT_ID')
    secret = os.getenv('PLAID_SECRET')
    access_token = os.getenv('PLAID_ACCESS_TOKEN')  # You'd get this after Link flow
    
    if not all([client_id, secret]):
        print("Please set PLAID_CLIENT_ID and PLAID_SECRET environment variables")
        return
    
    # Initialize client
    plaid_client = PlaidClient(client_id, secret, environment='sandbox')
    
    # Create link token (for initial setup)
    try:
        link_token_response = plaid_client.create_link_token(user_id="user_123")
        print(f"Link Token: {link_token_response['link_token']}")
    except Exception as e:
        print(f"Error: {e}")
    
    # If you have an access token, fetch data
    if access_token:
        try:
            # Get credit card data
            credit_data = plaid_client.get_credit_card_data(access_token)
            
            print(f"\n=== Credit Card Summary ===")
            print(f"Total Cards: {credit_data['total_cards']}")
            print(f"Total Balance: ${credit_data['total_balance']:.2f}")
            print(f"Total Limit: ${credit_data['total_limit']:.2f}")
            
            print(f"\n=== Individual Cards ===")
            for card in credit_data['credit_cards']:
                print(f"\n{card['name']}")
                print(f"  Balance: ${card['current_balance']:.2f}")
                print(f"  Limit: ${card['credit_limit']:.2f}")
                print(f"  Utilization: {card['utilization_percent']:.1f}%")
            
            print(f"\n=== Recent Transactions ===")
            for txn in credit_data['transactions'][:10]:
                print(f"{txn['date']}: {txn['name']} - ${txn['amount']:.2f}")
                
        except Exception as e:
            print(f"Error fetching data: {e}")


if __name__ == "__main__":
    main()
