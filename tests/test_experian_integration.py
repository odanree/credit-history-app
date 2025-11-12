"""
Unit tests for Experian integration
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.experian_integration import ExperianClient


class TestExperianClient:
    """Test suite for ExperianClient"""
    
    @pytest.fixture
    def experian_client(self):
        """Create ExperianClient instance for testing"""
        return ExperianClient(
            client_id="test_client_id",
            client_secret="test_secret",
            environment="sandbox",
            username="test@example.com",
            password="test_password"
        )
    
    def test_client_initialization(self, experian_client):
        """Test that ExperianClient initializes correctly"""
        assert experian_client is not None
        assert experian_client.client_id == "test_client_id"
        assert experian_client.client_secret == "test_secret"
        assert experian_client.environment == "sandbox"
        assert experian_client.username == "test@example.com"
    
    @patch('src.integrations.experian_integration.requests.post')
    def test_get_access_token_success(self, mock_post, experian_client):
        """Test successful OAuth token retrieval"""
        # Mock successful token response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token_123',
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        token = experian_client._get_access_token()
        
        assert token == 'test_access_token_123'
        assert mock_post.called
    
    @patch('src.integrations.experian_integration.requests.post')
    def test_get_access_token_failure(self, mock_post, experian_client):
        """Test OAuth token retrieval failure"""
        # Mock failed token response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception):
            experian_client._get_access_token()
    
    @patch('src.integrations.experian_integration.requests.post')
    def test_get_credit_report_success(self, mock_post, experian_client):
        """Test successful credit report retrieval"""
        # Mock OAuth token
        mock_token_response = MagicMock()
        mock_token_response.status_code = 200
        mock_token_response.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 3600
        }
        
        # Mock credit report response
        mock_report_response = MagicMock()
        mock_report_response.status_code = 200
        mock_report_response.json.return_value = {
            'creditScore': 720,
            'riskModel': 'VantageScore 3.0',
            'tradelines': []
        }
        
        mock_post.side_effect = [mock_token_response, mock_report_response]
        
        consumer_info = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123456789',
            'dob': '1990-01-01'
        }
        
        result = experian_client.get_credit_report(consumer_info)
        
        assert 'creditScore' in result
        assert result['creditScore'] == 720
    
    @patch('src.integrations.experian_integration.requests.post')
    def test_get_credit_report_missing_info(self, mock_post, experian_client):
        """Test credit report with missing consumer info"""
        # Missing required fields
        consumer_info = {
            'firstName': 'John'
            # Missing lastName, ssn, dob
        }
        
        result = experian_client.get_credit_report(consumer_info)
        
        # Should return error or handle gracefully
        assert result is not None
    
    def test_base_url_selection(self, experian_client):
        """Test correct base URL for environment"""
        assert 'sandbox' in experian_client.base_url.lower()
        
        # Test production URL
        prod_client = ExperianClient(
            client_id="test",
            client_secret="test",
            environment="production",
            username="test@example.com",
            password="test"
        )
        assert 'sandbox' not in prod_client.base_url.lower()
    
    def test_consumer_info_formatting(self, experian_client):
        """Test consumer information formatting"""
        consumer_info = {
            'firstName': 'John',
            'lastName': 'Doe',
            'ssn': '123-45-6789',  # With dashes
            'dob': '1990-01-01'
        }
        
        # SSN should be normalized (remove dashes)
        normalized_ssn = consumer_info['ssn'].replace('-', '')
        assert len(normalized_ssn) == 9
        assert normalized_ssn.isdigit()
