"""
Experian Connect API Integration
Fetches credit reports, scores, and credit history
"""

import os
import requests
import base64
from typing import Dict, Optional
from datetime import datetime


class ExperianClient:
    """Client for interacting with Experian Connect API"""
    
    def __init__(self, client_id: str, client_secret: str, environment: str = "sandbox"):
        """
        Initialize Experian client
        
        Args:
            client_id: Your Experian client ID
            client_secret: Your Experian client secret
            environment: 'sandbox' or 'production'
        """
        self.client_id = client_id
        self.client_secret = client_secret
        
        self.base_urls = {
            'sandbox': 'https://sandbox-us-api.experian.com',
            'production': 'https://us-api.experian.com'
        }
        self.base_url = self.base_urls.get(environment, self.base_urls['sandbox'])
        self.access_token = None
        self.token_expiry = None
    
    def _get_access_token(self) -> str:
        """
        Get OAuth access token for API calls
        
        Returns:
            Access token string
        """
        # Check if we have a valid token
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token
        
        # Request new token
        auth_url = f"{self.base_url}/oauth2/v1/token"
        
        # Create Basic Auth header
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'client_credentials'
        }
        
        try:
            response = requests.post(auth_url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data['access_token']
            # Set expiry to 5 minutes before actual expiry
            expires_in = token_data.get('expires_in', 3600) - 300
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            return self.access_token
        except requests.exceptions.RequestException as e:
            print(f"Error getting access token: {e}")
            raise
    
    def get_credit_report(
        self, 
        consumer_info: Dict,
        include_score: bool = True
    ) -> Dict:
        """
        Get full credit report for a consumer
        
        Args:
            consumer_info: Dict containing consumer information:
                {
                    'firstName': 'John',
                    'lastName': 'Doe',
                    'ssn': '123456789',
                    'dob': '1980-01-01',
                    'address': {
                        'line1': '123 Main St',
                        'city': 'New York',
                        'state': 'NY',
                        'zip': '10001'
                    }
                }
            include_score: Whether to include credit score
            
        Returns:
            Dict containing credit report data
        """
        token = self._get_access_token()
        
        url = f"{self.base_url}/consumerservices/credit-profile/v2/credit-report"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'consumerPii': consumer_info,
            'requestor': {
                'subscriberCode': self.client_id
            },
            'permissiblePurpose': {
                'type': 'OwnCredit',  # Consumer requesting their own credit
                'terms': 'Y'
            },
            'addOns': {
                'scoreIndicator': include_score
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching credit report: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise
    
    def get_credit_score(self, consumer_info: Dict) -> Dict:
        """
        Get just the credit score (VantageScore or FICO)
        
        Args:
            consumer_info: Consumer identification information
            
        Returns:
            Dict containing credit score information
        """
        report = self.get_credit_report(consumer_info, include_score=True)
        
        # Extract score from report
        if 'creditReport' in report and 'riskModel' in report['creditReport']:
            scores = report['creditReport']['riskModel']
            return {
                'score': scores.get('score'),
                'scoreFactors': scores.get('scoreFactors', []),
                'modelIndicator': scores.get('modelIndicator'),
                'score_date': datetime.now().isoformat()
            }
        
        return {'error': 'Score not found in report'}
    
    def get_trade_lines(self, consumer_info: Dict) -> Dict:
        """
        Get all credit accounts (trade lines) from credit report
        
        Args:
            consumer_info: Consumer identification information
            
        Returns:
            Dict containing all credit accounts with payment history
        """
        report = self.get_credit_report(consumer_info)
        
        trade_lines = []
        
        if 'creditReport' in report and 'tradeline' in report['creditReport']:
            for tradeline in report['creditReport']['tradeline']:
                account = {
                    'creditor': tradeline.get('creditorName'),
                    'account_type': tradeline.get('accountType'),
                    'account_number': tradeline.get('accountNumber', 'N/A')[-4:],  # Last 4 digits
                    'open_date': tradeline.get('dateOpened'),
                    'status': tradeline.get('accountStatus'),
                    'balance': tradeline.get('balance'),
                    'credit_limit': tradeline.get('highCredit'),
                    'payment_status': tradeline.get('paymentStatus'),
                    'payment_history': tradeline.get('paymentHistory', []),
                    'last_payment_date': tradeline.get('lastPaymentDate'),
                    'monthly_payment': tradeline.get('monthlyPayment')
                }
                
                # Calculate utilization for revolving accounts
                if account['credit_limit'] and account['balance']:
                    account['utilization'] = (
                        account['balance'] / account['credit_limit'] * 100
                    )
                
                trade_lines.append(account)
        
        return {
            'total_accounts': len(trade_lines),
            'accounts': trade_lines,
            'retrieved_date': datetime.now().isoformat()
        }
    
    def get_credit_summary(self, consumer_info: Dict) -> Dict:
        """
        Get comprehensive credit summary including score, accounts, and key metrics
        
        Args:
            consumer_info: Consumer identification information
            
        Returns:
            Dict containing complete credit summary
        """
        report = self.get_credit_report(consumer_info, include_score=True)
        
        summary = {
            'credit_score': None,
            'total_accounts': 0,
            'open_accounts': 0,
            'closed_accounts': 0,
            'total_balance': 0,
            'total_credit_limit': 0,
            'overall_utilization': 0,
            'delinquent_accounts': 0,
            'hard_inquiries': 0,
            'public_records': 0,
            'accounts': [],
            'report_date': datetime.now().isoformat()
        }
        
        if 'creditReport' not in report:
            return summary
        
        credit_report = report['creditReport']
        
        # Extract credit score
        if 'riskModel' in credit_report:
            summary['credit_score'] = credit_report['riskModel'].get('score')
        
        # Extract trade lines
        if 'tradeline' in credit_report:
            trade_lines = credit_report['tradeline']
            summary['total_accounts'] = len(trade_lines)
            
            total_balance = 0
            total_limit = 0
            
            for tl in trade_lines:
                status = tl.get('accountStatus', '').lower()
                if 'open' in status:
                    summary['open_accounts'] += 1
                else:
                    summary['closed_accounts'] += 1
                
                balance = tl.get('balance', 0) or 0
                limit = tl.get('highCredit', 0) or 0
                
                total_balance += balance
                total_limit += limit
                
                # Check for delinquencies
                if tl.get('paymentStatus') and tl['paymentStatus'] != 'C':
                    summary['delinquent_accounts'] += 1
                
                summary['accounts'].append({
                    'creditor': tl.get('creditorName'),
                    'type': tl.get('accountType'),
                    'balance': balance,
                    'limit': limit,
                    'status': tl.get('accountStatus')
                })
            
            summary['total_balance'] = total_balance
            summary['total_credit_limit'] = total_limit
            
            if total_limit > 0:
                summary['overall_utilization'] = round(
                    (total_balance / total_limit) * 100, 2
                )
        
        # Extract inquiries
        if 'inquiry' in credit_report:
            summary['hard_inquiries'] = len([
                inq for inq in credit_report['inquiry']
                if inq.get('type') == 'hard'
            ])
        
        # Extract public records
        if 'publicRecord' in credit_report:
            summary['public_records'] = len(credit_report['publicRecord'])
        
        return summary


def main():
    """Example usage"""
    # Load from environment variables
    client_id = os.getenv('EXPERIAN_CLIENT_ID')
    client_secret = os.getenv('EXPERIAN_CLIENT_SECRET')
    
    if not all([client_id, client_secret]):
        print("Please set EXPERIAN_CLIENT_ID and EXPERIAN_CLIENT_SECRET environment variables")
        return
    
    # Initialize client
    experian = ExperianClient(client_id, client_secret, environment='sandbox')
    
    # Example consumer info (use real data in production)
    consumer_info = {
        'firstName': 'John',
        'lastName': 'Doe',
        'ssn': '666112222',  # Sandbox test SSN
        'dob': '1980-01-01',
        'address': {
            'line1': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'zip': '10001'
        }
    }
    
    try:
        # Get credit summary
        print("Fetching credit summary...")
        summary = experian.get_credit_summary(consumer_info)
        
        print(f"\n=== Credit Summary ===")
        print(f"Credit Score: {summary['credit_score']}")
        print(f"Total Accounts: {summary['total_accounts']}")
        print(f"Open Accounts: {summary['open_accounts']}")
        print(f"Total Balance: ${summary['total_balance']:,.2f}")
        print(f"Total Credit Limit: ${summary['total_credit_limit']:,.2f}")
        print(f"Overall Utilization: {summary['overall_utilization']}%")
        print(f"Delinquent Accounts: {summary['delinquent_accounts']}")
        print(f"Hard Inquiries: {summary['hard_inquiries']}")
        
        print(f"\n=== Account Details ===")
        for account in summary['accounts'][:5]:  # Show first 5
            print(f"\n{account['creditor']}")
            print(f"  Type: {account['type']}")
            print(f"  Balance: ${account['balance']:,.2f}")
            print(f"  Status: {account['status']}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    from datetime import timedelta
    main()
