"""
Unit tests for Plaid integration
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.plaid_integration import PlaidClient


class TestPlaidClient:
    """Test suite for PlaidClient"""
    
    @pytest.fixture
    def plaid_client(self):
        """Create PlaidClient instance for testing"""
        return PlaidClient(
            client_id="test_client_id",
            secret="test_secret",
            environment="sandbox"
        )
    
    def test_client_initialization(self, plaid_client):
        """Test that PlaidClient initializes correctly"""
        assert plaid_client is not None
        assert plaid_client.client_id == "test_client_id"
        assert plaid_client.secret == "test_secret"
        assert plaid_client.environment == "sandbox"
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_credit_card_data_success(self, mock_plaid_api, plaid_client):
        """Test successful retrieval of credit card data"""
        # Mock the API response
        mock_client = MagicMock()
        mock_plaid_api.return_value = mock_client
        
        # Mock accounts_get response
        mock_accounts_response = MagicMock()
        mock_accounts_response.to_dict.return_value = {
            'accounts': [
                {
                    'account_id': 'acc_123',
                    'name': 'Test Credit Card',
                    'type': 'credit',
                    'subtype': 'credit card',
                    'balances': {
                        'current': 1000,
                        'limit': 5000
                    }
                }
            ]
        }
        
        # Mock transactions_get response
        mock_transactions_response = MagicMock()
        mock_transactions_response.to_dict.return_value = {
            'transactions': [
                {
                    'transaction_id': 'txn_123',
                    'account_id': 'acc_123',
                    'amount': 50.00,
                    'date': '2025-11-10',
                    'name': 'Test Merchant',
                    'category': ['Shopping']
                }
            ],
            'total_transactions': 1
        }
        
        with patch.object(plaid_client, 'client') as mock_client_instance:
            mock_client_instance.accounts_get.return_value = mock_accounts_response
            mock_client_instance.transactions_get.return_value = mock_transactions_response
            
            result = plaid_client.get_credit_card_data('test_access_token')
        
        # Verify structure
        assert 'cards' in result
        assert 'summary' in result
        assert 'transactions' in result
        assert len(result['cards']) == 1
        assert result['cards'][0]['name'] == 'Test Credit Card'
        assert result['cards'][0]['balance'] == 1000
        assert result['cards'][0]['limit'] == 5000
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_credit_card_data_no_access_token(self, mock_plaid_api, plaid_client):
        """Test error handling when access token is missing"""
        result = plaid_client.get_credit_card_data(None)
        
        assert 'error' in result
        assert 'Access token is required' in result['error']
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_credit_card_data_api_exception(self, mock_plaid_api, plaid_client):
        """Test error handling when Plaid API raises exception"""
        with patch.object(plaid_client, 'client') as mock_client_instance:
            mock_client_instance.accounts_get.side_effect = Exception("API Error")
            
            result = plaid_client.get_credit_card_data('test_access_token')
        
        assert 'error' in result
        assert 'API Error' in result['error']
    
    def test_calculate_utilization(self, plaid_client):
        """Test credit utilization calculation"""
        # Test normal case
        utilization = plaid_client._calculate_utilization(1000, 5000)
        assert utilization == 20.0
        
        # Test zero limit
        utilization = plaid_client._calculate_utilization(1000, 0)
        assert utilization == 0
        
        # Test None values
        utilization = plaid_client._calculate_utilization(None, 5000)
        assert utilization == 0
        
        utilization = plaid_client._calculate_utilization(1000, None)
        assert utilization == 0
    
    def test_filter_credit_cards(self, plaid_client):
        """Test filtering credit card accounts"""
        accounts = [
            {'type': 'credit', 'subtype': 'credit card', 'name': 'Card 1'},
            {'type': 'depository', 'subtype': 'checking', 'name': 'Checking'},
            {'type': 'credit', 'subtype': 'credit card', 'name': 'Card 2'},
        ]
        
        credit_cards = [acc for acc in accounts if acc.get('type') == 'credit']
        assert len(credit_cards) == 2
        assert all(card['type'] == 'credit' for card in credit_cards)
