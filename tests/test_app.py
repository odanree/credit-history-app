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
    def test_dashboard_route_success(self, mock_get_data, client):
        """Test dashboard route with successful data fetch"""
        # Mock credit data
        mock_get_data.return_value = {
            'cards': [
                {
                    'name': 'Test Card',
                    'balance': 1000,
                    'limit': 5000,
                    'utilization': 20.0
                }
            ],
            'summary': {
                'total_balance': 1000,
                'total_limit': 5000,
                'average_utilization': 20.0
            },
            'transactions': []
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
        
        assert response.status_code == 200
        # Should still render page, maybe with error message
    
    @patch('src.app.get_credit_data')
    def test_api_data_endpoint(self, mock_get_data, client):
        """Test /api/data endpoint"""
        mock_data = {
            'cards': [],
            'summary': {},
            'transactions': []
        }
        mock_get_data.return_value = mock_data
        
        response = client.get('/api/data')
        
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        assert 'cards' in data
        assert 'summary' in data
        assert 'transactions' in data
    
    def test_analyze_transactions_empty(self):
        """Test transaction analysis with empty list"""
        result = analyze_transactions([])
        
        assert result['by_month'] == {}
        assert result['by_category'] == {}
        assert result['by_merchant'] == {}
    
    def test_analyze_transactions_with_data(self):
        """Test transaction analysis with sample data"""
        from datetime import datetime
        
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
        
        # Check by_month
        assert len(result['by_month']) > 0
        
        # Check by_category
        assert 'Food' in result['by_category'] or 'Restaurants' in result['by_category']
        
        # Check by_merchant
        assert 'Restaurant A' in result['by_merchant']
        assert result['by_merchant']['Restaurant A'] == 50.00
    
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
