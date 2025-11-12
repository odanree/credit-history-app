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


class TestExperianTokenCaching:
    """Tests for OAuth token caching"""
    
    @pytest.fixture
    def experian_client(self):
        return ExperianClient(
            client_id="test_client_id",
            client_secret="test_secret",
            environment="sandbox",
            username="test@example.com",
            password="test_password"
        )
    
    @patch('src.integrations.experian_integration.requests.post')
    def test_token_caching(self, mock_post, experian_client):
        """Test that token is cached and reused"""
        from datetime import datetime, timedelta
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'cached_token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        # First call should request token
        token1 = experian_client._get_access_token()
        assert token1 == 'cached_token'
        assert mock_post.call_count == 1
        
        # Second call should use cached token
        token2 = experian_client._get_access_token()
        assert token2 == 'cached_token'
        assert mock_post.call_count == 1  # No additional call
    
    @patch('src.integrations.experian_integration.requests.post')
    def test_token_refresh_on_expiry(self, mock_post, experian_client):
        """Test that expired token is refreshed"""
        from datetime import datetime, timedelta
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'new_token',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response
        
        # Set expired token
        experian_client.access_token = 'old_token'
        experian_client.token_expiry = datetime.now() - timedelta(seconds=1)
        
        # Should request new token
        token = experian_client._get_access_token()
        assert token == 'new_token'
        assert mock_post.called
    
    @patch('src.integrations.experian_integration.requests.post')
    def test_error_response_handling(self, mock_post, experian_client):
        """Test handling of non-200 error responses"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "Bad Request"}'
        mock_response.raise_for_status.side_effect = Exception("Bad Request")
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception):
            experian_client._get_access_token()


class TestExperianCreditMethods:
    """Tests for credit report parsing methods"""
    
    @pytest.fixture
    def experian_client(self):
        return ExperianClient(
            client_id="test_client_id",
            client_secret="test_secret",
            environment="sandbox",
            username="test@example.com",
            password="test_password"
        )
    
    @patch('src.integrations.experian_integration.ExperianClient.get_credit_report')
    def test_get_credit_score_success(self, mock_get_report, experian_client):
        """Test extracting credit score from report"""
        mock_get_report.return_value = {
            'creditReport': {
                'riskModel': {
                    'score': 750,
                    'scoreFactors': ['Low credit utilization'],
                    'modelIndicator': 'VantageScore 3.0'
                }
            }
        }
        
        consumer_info = {'firstName': 'John', 'lastName': 'Doe'}
        result = experian_client.get_credit_score(consumer_info)
        
        assert result['score'] == 750
        assert 'scoreFactors' in result
        assert 'modelIndicator' in result
    
    @patch('src.integrations.experian_integration.ExperianClient.get_credit_report')
    def test_get_credit_score_not_found(self, mock_get_report, experian_client):
        """Test handling when score is not in report"""
        mock_get_report.return_value = {'creditReport': {}}
        
        consumer_info = {'firstName': 'John', 'lastName': 'Doe'}
        result = experian_client.get_credit_score(consumer_info)
        
        assert 'error' in result
    
    @patch('src.integrations.experian_integration.ExperianClient.get_credit_report')
    def test_get_trade_lines_success(self, mock_get_report, experian_client):
        """Test extracting trade lines from report"""
        mock_get_report.return_value = {
            'creditReport': {
                'tradeline': [
                    {
                        'creditorName': 'Chase Bank',
                        'accountType': 'Credit Card',
                        'accountNumber': '1234567890',
                        'dateOpened': '2020-01-01',
                        'accountStatus': 'Open',
                        'balance': 1000,
                        'highCredit': 5000,
                        'paymentStatus': 'C',
                        'monthlyPayment': 50
                    },
                    {
                        'creditorName': 'Capital One',
                        'accountType': 'Credit Card',
                        'balance': 500,
                        'highCredit': 2000
                    }
                ]
            }
        }
        
        consumer_info = {'firstName': 'John', 'lastName': 'Doe'}
        result = experian_client.get_trade_lines(consumer_info)
        
        assert result['total_accounts'] == 2
        assert len(result['accounts']) == 2
        assert result['accounts'][0]['creditor'] == 'Chase Bank'
        assert result['accounts'][0]['utilization'] == 20.0  # 1000/5000 * 100
    
    @patch('src.integrations.experian_integration.ExperianClient.get_credit_report')
    def test_get_trade_lines_empty(self, mock_get_report, experian_client):
        """Test handling empty trade lines"""
        mock_get_report.return_value = {'creditReport': {}}
        
        consumer_info = {'firstName': 'John', 'lastName': 'Doe'}
        result = experian_client.get_trade_lines(consumer_info)
        
        assert result['total_accounts'] == 0
        assert result['accounts'] == []
    
    @patch('src.integrations.experian_integration.ExperianClient.get_credit_report')
    def test_get_credit_summary_comprehensive(self, mock_get_report, experian_client):
        """Test comprehensive credit summary"""
        mock_get_report.return_value = {
            'creditReport': {
                'riskModel': {'score': 720},
                'tradeline': [
                    {
                        'creditorName': 'Bank A',
                        'accountType': 'Credit Card',
                        'accountStatus': 'Open',
                        'balance': 2000,
                        'highCredit': 5000,
                        'paymentStatus': 'C'
                    },
                    {
                        'creditorName': 'Bank B',
                        'accountType': 'Auto Loan',
                        'accountStatus': 'Closed',
                        'balance': 0,
                        'highCredit': 20000,
                        'paymentStatus': '30'  # 30 days late
                    }
                ],
                'inquiry': [
                    {'type': 'hard', 'date': '2024-01-01'},
                    {'type': 'soft', 'date': '2024-02-01'}
                ],
                'publicRecord': [
                    {'type': 'Bankruptcy', 'date': '2020-01-01'}
                ]
            }
        }
        
        consumer_info = {'firstName': 'John', 'lastName': 'Doe'}
        result = experian_client.get_credit_summary(consumer_info)
        
        assert result['credit_score'] == 720
        assert result['total_accounts'] == 2
        assert result['open_accounts'] == 1
        assert result['closed_accounts'] == 1
        assert result['total_balance'] == 2000
        assert result['total_credit_limit'] == 25000
        assert result['overall_utilization'] == 8.0  # 2000/25000 * 100
        assert result['delinquent_accounts'] == 1  # Bank B with '30' status
        assert result['hard_inquiries'] == 1
        assert result['public_records'] == 1
    
    @patch('src.integrations.experian_integration.ExperianClient.get_credit_report')
    def test_get_credit_summary_empty_report(self, mock_get_report, experian_client):
        """Test credit summary with empty report"""
        mock_get_report.return_value = {}
        
        consumer_info = {'firstName': 'John', 'lastName': 'Doe'}
        result = experian_client.get_credit_summary(consumer_info)
        
        assert result['credit_score'] is None
        assert result['total_accounts'] == 0
        assert result['overall_utilization'] == 0
