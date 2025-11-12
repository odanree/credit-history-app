"""
Pytest configuration and fixtures
"""
import pytest
import sys
import os

# Add parent directory to path for all tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope='session')
def test_env_vars():
    """Set up test environment variables"""
    os.environ['PLAID_CLIENT_ID'] = 'test_client_id'
    os.environ['PLAID_SECRET'] = 'test_secret'
    os.environ['PLAID_ENV'] = 'sandbox'
    os.environ['PLAID_ACCESS_TOKEN'] = 'test_access_token'
    os.environ['EXPERIAN_CLIENT_ID'] = 'test_experian_id'
    os.environ['EXPERIAN_CLIENT_SECRET'] = 'test_experian_secret'
    os.environ['EXPERIAN_ENV'] = 'sandbox'
    
    yield
    
    # Cleanup after tests
    for key in ['PLAID_CLIENT_ID', 'PLAID_SECRET', 'PLAID_ENV', 
                'PLAID_ACCESS_TOKEN', 'EXPERIAN_CLIENT_ID', 
                'EXPERIAN_CLIENT_SECRET', 'EXPERIAN_ENV']:
        os.environ.pop(key, None)
