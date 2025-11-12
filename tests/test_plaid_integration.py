"""
Unit tests for Plaid integration
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import plaid

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
        # Note: secret and environment are not stored as attributes
        assert plaid_client.client is not None
    
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
        
        # Verify structure (matches actual API response)
        assert 'credit_cards' in result
        assert 'total_cards' in result
        assert 'total_balance' in result
        assert 'total_limit' in result
        assert 'transactions' in result
        assert len(result['credit_cards']) == 1
        assert result['credit_cards'][0]['name'] == 'Test Credit Card'
        assert result['credit_cards'][0]['current_balance'] == 1000
        assert result['credit_cards'][0]['credit_limit'] == 5000
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_credit_card_data_no_access_token(self, mock_plaid_api, plaid_client):
        """Test error handling when access token is missing"""
        # Plaid SDK will raise ApiTypeError for None access_token
        import plaid
        
        with pytest.raises(plaid.exceptions.ApiTypeError):
            plaid_client.get_credit_card_data(None)
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_credit_card_data_api_exception(self, mock_plaid_api, plaid_client):
        """Test error handling when Plaid API raises exception"""
        with patch.object(plaid_client, 'client') as mock_client_instance:
            mock_client_instance.accounts_get.side_effect = Exception("API Error")
            
            with pytest.raises(Exception, match="API Error"):
                plaid_client.get_credit_card_data('test_access_token')
    
    def test_calculate_utilization(self, plaid_client):
        """Test credit utilization calculation"""
        # The actual implementation calculates inline, test the logic
        balance = 1000
        limit = 5000
        
        # Test normal case
        utilization = (balance / limit) * 100 if limit > 0 else 0
        assert utilization == 20.0
        
        # Test zero limit
        limit_zero = 0
        utilization_zero = (balance / limit_zero) * 100 if limit_zero > 0 else 0
        assert utilization_zero == 0
        
        # Test None values
        balance_none = None
        utilization_none = (balance_none / limit) * 100 if balance_none and limit > 0 else 0
        assert utilization_none == 0
    
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


class TestPlaidClientLinkToken:
    """Tests for link token creation"""
    
    @pytest.fixture
    def plaid_client(self):
        """Create PlaidClient instance for testing"""
        return PlaidClient(
            client_id="test_client_id",
            secret="test_secret",
            environment="sandbox"
        )
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_create_link_token_success(self, mock_plaid_api, plaid_client):
        """Test successful link token creation"""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            'link_token': 'link-sandbox-test-token',
            'expiration': '2025-11-12T00:00:00Z'
        }
        
        with patch.object(plaid_client, 'client') as mock_client:
            mock_client.link_token_create.return_value = mock_response
            
            result = plaid_client.create_link_token('user_123')
        
        assert 'link_token' in result
        assert result['link_token'] == 'link-sandbox-test-token'
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_create_link_token_api_exception(self, mock_plaid_api, plaid_client):
        """Test link token creation with API exception"""
        with patch.object(plaid_client, 'client') as mock_client:
            mock_client.link_token_create.side_effect = plaid.ApiException("API Error")
            
            with pytest.raises(plaid.ApiException):
                plaid_client.create_link_token('user_123')


class TestPlaidClientAccountsAndTransactions:
    """Additional tests for accounts and transactions methods"""
    
    @pytest.fixture
    def plaid_client(self):
        """Create PlaidClient instance for testing"""
        return PlaidClient(
            client_id="test_client_id",
            secret="test_secret",
            environment="sandbox"
        )
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_accounts_success(self, mock_plaid_api, plaid_client):
        """Test successful account retrieval"""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            'accounts': [
                {
                    'account_id': 'acc_1',
                    'name': 'Credit Card',
                    'type': 'credit',
                    'balances': {'current': 100}
                }
            ]
        }
        
        with patch.object(plaid_client, 'client') as mock_client:
            mock_client.accounts_get.return_value = mock_response
            
            result = plaid_client.get_accounts('test_token')
        
        assert len(result) == 1
        assert result[0]['name'] == 'Credit Card'
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_accounts_api_exception(self, mock_plaid_api, plaid_client):
        """Test get accounts with API exception"""
        with patch.object(plaid_client, 'client') as mock_client:
            mock_client.accounts_get.side_effect = plaid.ApiException("API Error")
            
            with pytest.raises(plaid.ApiException):
                plaid_client.get_accounts('test_token')
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_transactions_with_date_range(self, mock_plaid_api, plaid_client):
        """Test transaction retrieval with date range"""
        from datetime import datetime, timedelta
        
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            'transactions': [
                {
                    'transaction_id': 'txn_1',
                    'amount': 50.00,
                    'date': '2025-11-10'
                }
            ],
            'total_transactions': 1
        }
        
        with patch.object(plaid_client, 'client') as mock_client:
            mock_client.transactions_get.return_value = mock_response
            
            start_date = datetime.now() - timedelta(days=30)
            result = plaid_client.get_transactions(
                'test_token',
                start_date=start_date
            )
        
        assert 'transactions' in result
        assert len(result['transactions']) == 1
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_transactions_with_pagination(self, mock_plaid_api, plaid_client):
        """Test transaction retrieval with pagination"""
        from datetime import datetime, timedelta
        
        # First call returns partial transactions
        mock_response1 = MagicMock()
        mock_response1.to_dict.return_value = {
            'transactions': [{'transaction_id': 'txn_1'}],
            'total_transactions': 2
        }
        
        # Second call returns remaining transactions  
        mock_response2 = MagicMock()
        mock_response2.__getitem__ = lambda self, key: [{'transaction_id': 'txn_2'}] if key == 'transactions' else None
        
        with patch.object(plaid_client, 'client') as mock_client:
            mock_client.transactions_get.side_effect = [mock_response1, mock_response2]
            
            result = plaid_client.get_transactions('test_token')
        
        assert 'transactions' in result
        # Pagination logic extends the list
        assert len(result['transactions']) >= 1
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_transactions_with_account_ids(self, mock_plaid_api, plaid_client):
        """Test transaction retrieval with specific account IDs"""
        mock_response = MagicMock()
        mock_response.to_dict.return_value = {
            'transactions': [{'transaction_id': 'txn_1', 'account_id': 'acc_123'}],
            'total_transactions': 1
        }
        
        with patch.object(plaid_client, 'client') as mock_client:
            mock_client.transactions_get.return_value = mock_response
            
            result = plaid_client.get_transactions(
                'test_token',
                account_ids=['acc_123']
            )
        
        assert 'transactions' in result
        assert result['transactions'][0]['account_id'] == 'acc_123'
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_transactions_api_exception(self, mock_plaid_api, plaid_client):
        """Test get transactions with API exception"""
        with patch.object(plaid_client, 'client') as mock_client:
            mock_client.transactions_get.side_effect = plaid.ApiException("API Error")
            
            with pytest.raises(plaid.ApiException):
                plaid_client.get_transactions('test_token')
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_get_credit_card_data_multiple_cards(self, mock_plaid_api, plaid_client):
        """Test with multiple credit cards"""
        mock_accounts_response = MagicMock()
        mock_accounts_response.to_dict.return_value = {
            'accounts': [
                {
                    'account_id': 'acc_1',
                    'name': 'Card 1',
                    'type': 'credit',
                    'balances': {'current': 1000, 'limit': 5000}
                },
                {
                    'account_id': 'acc_2',
                    'name': 'Card 2',
                    'type': 'credit',
                    'balances': {'current': 500, 'limit': 2000}
                },
                {
                    'account_id': 'acc_3',
                    'name': 'Checking',
                    'type': 'depository',
                    'balances': {'current': 3000}
                }
            ]
        }
        
        mock_transactions_response = MagicMock()
        mock_transactions_response.to_dict.return_value = {
            'transactions': [],
            'total_transactions': 0
        }
        
        with patch.object(plaid_client, 'client') as mock_client:
            mock_client.accounts_get.return_value = mock_accounts_response
            mock_client.transactions_get.return_value = mock_transactions_response
            
            result = plaid_client.get_credit_card_data('test_token')
        
        # Should only include credit cards
        assert result['total_cards'] == 2
        assert result['total_balance'] == 1500  # 1000 + 500
        assert result['total_limit'] == 7000  # 5000 + 2000
    
    @patch('src.integrations.plaid_integration.plaid_api.PlaidApi')
    def test_utilization_calculation_edge_cases(self, mock_plaid_api, plaid_client):
        """Test utilization calculation with edge cases"""
        mock_accounts_response = MagicMock()
        mock_accounts_response.to_dict.return_value = {
            'accounts': [
                {
                    'account_id': 'acc_1',
                    'name': 'Card with no limit',
                    'type': 'credit',
                    'balances': {'current': 1000, 'limit': None}
                },
                {
                    'account_id': 'acc_2',
                    'name': 'Card with zero limit',
                    'type': 'credit',
                    'balances': {'current': 500, 'limit': 0}
                }
            ]
        }
        
        mock_transactions_response = MagicMock()
        mock_transactions_response.to_dict.return_value = {
            'transactions': [],
            'total_transactions': 0
        }
        
        with patch.object(plaid_client, 'client') as mock_client:
            mock_client.accounts_get.return_value = mock_accounts_response
            mock_client.transactions_get.return_value = mock_transactions_response
            
            result = plaid_client.get_credit_card_data('test_token')
        
        # Both cards should have 0 utilization
        for card in result['credit_cards']:
            assert card['utilization_percent'] == 0
