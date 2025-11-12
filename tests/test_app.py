"""
Unit tests for Flask app
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app import app, get_credit_data, analyze_transactions


@pytest.fixture
def client():
    """Create Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestFlaskApp:
    """Test suite for Flask application"""
    
    def test_app_exists(self):
        """Test that Flask app instance exists"""
        assert app is not None
    
    def test_app_is_testing(self, client):
        """Test that app is in testing mode"""
        assert app.config['TESTING']
    
    @patch('src.app.get_credit_data')
    @patch('src.app.analyze_transactions')
    def test_dashboard_route_success(self, mock_analyze, mock_get_data, client):
        """Test dashboard route with successful data fetch"""
        # Mock credit data matching actual API structure
        mock_get_data.return_value = {
            'credit_cards': [
                {
                    'name': 'Test Card',
                    'current_balance': 1000,
                    'credit_limit': 5000,
                    'utilization_percent': 20.0
                }
            ],
            'total_cards': 1,
            'total_balance': 1000,
            'total_limit': 5000,
            'transactions': []
        }
        
        # Mock analysis data to match template expectations
        mock_analyze.return_value = {
            'monthly_spending': {},
            'top_categories': [('Food', 100.00), ('Transport', 50.00)],
            'top_merchants': [('Merchant A', 75.00), ('Merchant B', 45.00)],
            'total_spent': 150.00
        }
        
        response = client.get('/')
        
        assert response.status_code == 200
        assert b'Test Card' in response.data
    
    @patch('src.app.get_credit_data')
    def test_dashboard_route_error(self, mock_get_data, client):
        """Test dashboard route with data fetch error"""
        # Mock error response
        mock_get_data.return_value = None
        
        response = client.get('/')
        
        # Should return 500 error with error message
        assert response.status_code == 500
        assert b'Error loading data' in response.data
    
    @patch('src.app.get_credit_data')
    def test_api_data_endpoint(self, mock_get_data, client):
        """Test /api/data endpoint"""
        mock_data = {
            'credit_cards': [],
            'total_cards': 0,
            'total_balance': 0,
            'total_limit': 0,
            'transactions': []
        }
        mock_get_data.return_value = mock_data
        
        response = client.get('/api/data')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        assert 'credit_cards' in data
        assert 'total_balance' in data
        assert 'transactions' in data
    
    def test_analyze_transactions_empty(self):
        """Test transaction analysis with empty list"""
        result = analyze_transactions([])
        
        # Empty list returns empty dict
        assert result == {}
    
    def test_analyze_transactions_with_data(self):
        """Test transaction analysis with sample data"""
        transactions = [
            {
                'date': '2025-11-10',
                'amount': 50.00,
                'category': ['Food', 'Restaurants'],
                'name': 'Restaurant A'
            },
            {
                'date': '2025-11-11',
                'amount': 30.00,
                'category': ['Food', 'Restaurants'],
                'name': 'Restaurant B'
            },
            {
                'date': '2025-10-15',
                'amount': 100.00,
                'category': ['Shopping'],
                'name': 'Store A'
            }
        ]
        
        result = analyze_transactions(transactions)
        
        # Check structure
        assert 'monthly_spending' in result
        assert 'top_categories' in result
        assert 'top_merchants' in result
        assert 'total_spent' in result
        
        # Check monthly spending
        assert '2025-11' in result['monthly_spending']
        assert '2025-10' in result['monthly_spending']
        
        # Check totals
        assert result['total_spent'] == 180.00  # 50 + 30 + 100
        
        # Check top merchants
        merchants = dict(result['top_merchants'])
        assert 'Restaurant A' in merchants
        assert merchants['Restaurant A'] == 50.00
    
    @patch.dict(os.environ, {
        'PLAID_CLIENT_ID': 'test_id',
        'PLAID_SECRET': 'test_secret',
        'PLAID_ENV': 'sandbox',
        'PLAID_ACCESS_TOKEN': 'test_token'
    })
    @patch('src.app.PlaidClient')
    def test_get_credit_data_success(self, mock_plaid_client):
        """Test get_credit_data with mocked Plaid client"""
        # Mock PlaidClient instance and response
        mock_client_instance = MagicMock()
        mock_client_instance.get_credit_card_data.return_value = {
            'cards': [{'name': 'Test Card'}],
            'summary': {},
            'transactions': []
        }
        mock_plaid_client.return_value = mock_client_instance
        
        result = get_credit_data()
        
        assert result is not None
        assert 'cards' in result
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_credit_data_missing_token(self):
        """Test get_credit_data with missing access token"""
        result = get_credit_data()
        
        assert result is None
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint if it exists"""
        response = client.get('/health')
        
        # Either 200 (exists) or 404 (doesn't exist yet)
        assert response.status_code in [200, 404]


class TestAnalyzeTransactions:
    """Additional tests for transaction analysis"""
    
    def test_analyze_with_datetime_objects(self):
        """Test transaction analysis with datetime objects"""
        from datetime import datetime
        
        transactions = [
            {
                'date': datetime(2025, 11, 10),
                'amount': 50.00,
                'category': ['Food'],
                'name': 'Test'
            }
        ]
        
        result = analyze_transactions(transactions)
        
        assert '2025-11' in result['monthly_spending']
        assert result['total_spent'] == 50.00
    
    def test_analyze_without_category(self):
        """Test transaction without category"""
        transactions = [
            {
                'date': '2025-11-10',
                'amount': 50.00,
                'name': 'Test Merchant'
            }
        ]
        
        result = analyze_transactions(transactions)
        
        # Should be categorized as 'Other'
        categories = dict(result['top_categories'])
        assert 'Other' in categories
    
    def test_analyze_with_nested_categories(self):
        """Test transaction with multiple category levels"""
        transactions = [
            {
                'date': '2025-11-10',
                'amount': 100.00,
                'category': ['Food', 'Restaurants', 'Fast Food'],
                'name': 'Restaurant'
            }
        ]
        
        result = analyze_transactions(transactions)
        
        # Should use first category level
        categories = dict(result['top_categories'])
        assert 'Food' in categories
        assert categories['Food'] == 100.00


class TestGetCreditData:
    """Additional tests for get_credit_data function"""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_all_credentials(self):
        """Test when all environment variables are missing"""
        result = get_credit_data()
        
        assert result is None
    
    @patch.dict(os.environ, {
        'PLAID_CLIENT_ID': 'test',
        'PLAID_SECRET': 'test',
        'PLAID_ENV': 'sandbox'
        # Missing PLAID_ACCESS_TOKEN
    })
    def test_missing_access_token_only(self):
        """Test when only access token is missing"""
        result = get_credit_data()
        
        assert result is None
    
    @patch.dict(os.environ, {
        'PLAID_CLIENT_ID': 'test_id',
        'PLAID_SECRET': 'test_secret',
        'PLAID_ENV': 'sandbox',
        'PLAID_ACCESS_TOKEN': 'test_token'
    })
    @patch('src.app.PlaidClient')
    def test_plaid_client_exception(self, mock_plaid_client):
        """Test when PlaidClient raises exception"""
        mock_client_instance = MagicMock()
        mock_client_instance.get_credit_card_data.side_effect = Exception("API Error")
        mock_plaid_client.return_value = mock_client_instance
        
        result = get_credit_data()
        
        assert result is None
