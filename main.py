"""
Main application combining Plaid and Experian APIs
Provides complete credit history including transactions and credit reports
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from plaid_integration import PlaidClient
from experian_integration import ExperianClient
import json


class CreditHistoryApp:
    """Main application for fetching complete credit history"""
    
    def __init__(self):
        """Initialize both Plaid and Experian clients"""
        load_dotenv()
        
        # Initialize Plaid
        self.plaid = PlaidClient(
            client_id=os.getenv('PLAID_CLIENT_ID'),
            secret=os.getenv('PLAID_SECRET'),
            environment=os.getenv('PLAID_ENV', 'sandbox')
        )
        
        # Initialize Experian
        self.experian = ExperianClient(
            client_id=os.getenv('EXPERIAN_CLIENT_ID'),
            client_secret=os.getenv('EXPERIAN_CLIENT_SECRET'),
            environment=os.getenv('EXPERIAN_ENV', 'sandbox')
        )
    
    def get_complete_credit_profile(
        self, 
        plaid_access_token: str,
        consumer_info: dict,
        transaction_days: int = 90
    ) -> dict:
        """
        Get complete credit profile combining Plaid and Experian data
        
        Args:
            plaid_access_token: Access token for Plaid API
            consumer_info: Consumer information for Experian
            transaction_days: Number of days of transaction history
            
        Returns:
            Complete credit profile dictionary
        """
        print("Fetching complete credit profile...")
        
        profile = {
            'generated_at': datetime.now().isoformat(),
            'plaid_data': {},
            'experian_data': {},
            'combined_summary': {}
        }
        
        # Get Plaid data (transactions and balances)
        print("\n1. Fetching transaction data from Plaid...")
        try:
            plaid_data = self.plaid.get_credit_card_data(
                plaid_access_token, 
                days=transaction_days
            )
            profile['plaid_data'] = plaid_data
            print(f"   ✓ Found {plaid_data['total_cards']} credit cards")
            print(f"   ✓ Retrieved {len(plaid_data['transactions'])} transactions")
        except Exception as e:
            print(f"   ✗ Error fetching Plaid data: {e}")
            profile['plaid_data'] = {'error': str(e)}
        
        # Get Experian data (credit report and score)
        print("\n2. Fetching credit report from Experian...")
        try:
            experian_data = self.experian.get_credit_summary(consumer_info)
            profile['experian_data'] = experian_data
            print(f"   ✓ Credit Score: {experian_data.get('credit_score')}")
            print(f"   ✓ Total Accounts: {experian_data.get('total_accounts')}")
            print(f"   ✓ Overall Utilization: {experian_data.get('overall_utilization')}%")
        except Exception as e:
            print(f"   ✗ Error fetching Experian data: {e}")
            profile['experian_data'] = {'error': str(e)}
        
        # Create combined summary
        print("\n3. Creating combined summary...")
        profile['combined_summary'] = self._create_combined_summary(
            profile['plaid_data'], 
            profile['experian_data']
        )
        
        return profile
    
    def _create_combined_summary(self, plaid_data: dict, experian_data: dict) -> dict:
        """Combine data from both sources into unified summary"""
        summary = {
            'credit_score': experian_data.get('credit_score'),
            'financial_snapshot': {
                'total_credit_cards': 0,
                'total_balance': 0,
                'total_credit_limit': 0,
                'overall_utilization': 0,
                'recent_transactions_count': 0,
                'monthly_spending': 0
            },
            'credit_health': {
                'open_accounts': experian_data.get('open_accounts', 0),
                'delinquent_accounts': experian_data.get('delinquent_accounts', 0),
                'hard_inquiries': experian_data.get('hard_inquiries', 0),
                'public_records': experian_data.get('public_records', 0)
            },
            'recommendations': []
        }
        
        # Combine balance data
        if 'error' not in plaid_data:
            summary['financial_snapshot']['total_credit_cards'] = plaid_data.get('total_cards', 0)
            summary['financial_snapshot']['total_balance'] = plaid_data.get('total_balance', 0)
            summary['financial_snapshot']['total_credit_limit'] = plaid_data.get('total_limit', 0)
            summary['financial_snapshot']['recent_transactions_count'] = len(plaid_data.get('transactions', []))
            
            # Calculate monthly spending from recent transactions
            transactions = plaid_data.get('transactions', [])
            if transactions:
                thirty_days_ago = (datetime.now() - timedelta(days=30)).date()
                recent_txns = [
                    t for t in transactions 
                    if datetime.fromisoformat(t.get('date', '2000-01-01')).date() >= thirty_days_ago
                ]
                summary['financial_snapshot']['monthly_spending'] = sum(
                    t.get('amount', 0) for t in recent_txns
                )
        
        # Use Experian utilization if Plaid data not available
        if summary['financial_snapshot']['overall_utilization'] == 0:
            summary['financial_snapshot']['overall_utilization'] = experian_data.get('overall_utilization', 0)
        elif summary['financial_snapshot']['total_credit_limit'] > 0:
            summary['financial_snapshot']['overall_utilization'] = round(
                (summary['financial_snapshot']['total_balance'] / 
                 summary['financial_snapshot']['total_credit_limit']) * 100, 2
            )
        
        # Generate recommendations
        summary['recommendations'] = self._generate_recommendations(summary)
        
        return summary
    
    def _generate_recommendations(self, summary: dict) -> list:
        """Generate actionable recommendations based on credit data"""
        recommendations = []
        
        credit_score = summary.get('credit_score')
        utilization = summary['financial_snapshot']['overall_utilization']
        delinquent = summary['credit_health']['delinquent_accounts']
        inquiries = summary['credit_health']['hard_inquiries']
        
        # Score-based recommendations
        if credit_score:
            if credit_score < 580:
                recommendations.append({
                    'priority': 'high',
                    'category': 'credit_score',
                    'message': 'Your credit score is in the poor range. Focus on paying bills on time and reducing debt.'
                })
            elif credit_score < 670:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'credit_score',
                    'message': 'Your credit score is fair. Continue building positive payment history.'
                })
            elif credit_score >= 740:
                recommendations.append({
                    'priority': 'low',
                    'category': 'credit_score',
                    'message': 'Great credit score! You qualify for the best rates and terms.'
                })
        
        # Utilization recommendations
        if utilization > 30:
            recommendations.append({
                'priority': 'high',
                'category': 'utilization',
                'message': f'Credit utilization is {utilization:.1f}%. Try to keep it below 30% by paying down balances.'
            })
        elif utilization > 10:
            recommendations.append({
                'priority': 'medium',
                'category': 'utilization',
                'message': f'Credit utilization is {utilization:.1f}%. Keeping it below 10% could improve your score.'
            })
        
        # Delinquency warnings
        if delinquent > 0:
            recommendations.append({
                'priority': 'critical',
                'category': 'payment_history',
                'message': f'You have {delinquent} delinquent account(s). Bring these current immediately to prevent further damage.'
            })
        
        # Hard inquiry notice
        if inquiries > 5:
            recommendations.append({
                'priority': 'medium',
                'category': 'inquiries',
                'message': f'You have {inquiries} hard inquiries. Avoid applying for new credit for a while.'
            })
        
        return recommendations
    
    def export_to_json(self, profile: dict, filename: str = None):
        """Export credit profile to JSON file"""
        if not filename:
            filename = f"credit_profile_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(os.getcwd(), filename)
        
        with open(filepath, 'w') as f:
            json.dump(profile, f, indent=2, default=str)
        
        print(f"\n✓ Profile exported to: {filepath}")
        return filepath
    
    def print_summary(self, profile: dict):
        """Print formatted summary of credit profile"""
        summary = profile.get('combined_summary', {})
        
        print("\n" + "="*60)
        print("COMPLETE CREDIT PROFILE SUMMARY")
        print("="*60)
        
        # Credit Score
        score = summary.get('credit_score')
        if score:
            print(f"\n📊 CREDIT SCORE: {score}")
            if score >= 740:
                rating = "Excellent"
            elif score >= 670:
                rating = "Good"
            elif score >= 580:
                rating = "Fair"
            else:
                rating = "Poor"
            print(f"   Rating: {rating}")
        
        # Financial Snapshot
        snapshot = summary.get('financial_snapshot', {})
        print(f"\n💳 CREDIT CARDS:")
        print(f"   Total Cards: {snapshot.get('total_credit_cards', 0)}")
        print(f"   Total Balance: ${snapshot.get('total_balance', 0):,.2f}")
        print(f"   Total Limit: ${snapshot.get('total_credit_limit', 0):,.2f}")
        print(f"   Utilization: {snapshot.get('overall_utilization', 0):.1f}%")
        print(f"   Monthly Spending: ${snapshot.get('monthly_spending', 0):,.2f}")
        print(f"   Recent Transactions: {snapshot.get('recent_transactions_count', 0)}")
        
        # Credit Health
        health = summary.get('credit_health', {})
        print(f"\n🏥 CREDIT HEALTH:")
        print(f"   Open Accounts: {health.get('open_accounts', 0)}")
        print(f"   Delinquent Accounts: {health.get('delinquent_accounts', 0)}")
        print(f"   Hard Inquiries: {health.get('hard_inquiries', 0)}")
        print(f"   Public Records: {health.get('public_records', 0)}")
        
        # Recommendations
        recommendations = summary.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                priority = rec['priority'].upper()
                emoji = "🔴" if priority == "CRITICAL" else "🟠" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
                print(f"   {emoji} [{priority}] {rec['message']}")
        
        print("\n" + "="*60)


def main():
    """Main entry point"""
    print("Credit History Application")
    print("Combining Plaid (transactions) + Experian (credit reports)")
    print("-" * 60)
    
    # Check environment variables
    required_vars = [
        'PLAID_CLIENT_ID', 'PLAID_SECRET',
        'EXPERIAN_CLIENT_ID', 'EXPERIAN_CLIENT_SECRET'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("\nPlease create a .env file with:")
        for var in required_vars:
            print(f"   {var}=your_value_here")
        return
    
    # Initialize app
    app = CreditHistoryApp()
    
    # Example usage (you'll need real access token and consumer info)
    plaid_access_token = os.getenv('PLAID_ACCESS_TOKEN')
    
    # Example consumer info for Experian (use real data)
    consumer_info = {
        'firstName': os.getenv('CONSUMER_FIRST_NAME', 'John'),
        'lastName': os.getenv('CONSUMER_LAST_NAME', 'Doe'),
        'ssn': os.getenv('CONSUMER_SSN', '666112222'),  # Sandbox test SSN
        'dob': os.getenv('CONSUMER_DOB', '1980-01-01'),
        'address': {
            'line1': os.getenv('CONSUMER_ADDRESS_LINE1', '123 Main St'),
            'city': os.getenv('CONSUMER_CITY', 'New York'),
            'state': os.getenv('CONSUMER_STATE', 'NY'),
            'zip': os.getenv('CONSUMER_ZIP', '10001')
        }
    }
    
    if not plaid_access_token:
        print("\n⚠️  PLAID_ACCESS_TOKEN not set. Will skip Plaid data.")
        print("   To get an access token, you need to complete the Plaid Link flow first.\n")
    
    try:
        # Get complete profile
        profile = app.get_complete_credit_profile(
            plaid_access_token or "dummy_token",
            consumer_info,
            transaction_days=90
        )
        
        # Print summary
        app.print_summary(profile)
        
        # Export to JSON
        export_choice = input("\nExport full profile to JSON? (y/n): ").lower()
        if export_choice == 'y':
            app.export_to_json(profile)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
