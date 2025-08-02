import os
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import pytz

class FCMService:
    def __init__(self):
        self.server_key = os.getenv('FIREBASE_SERVER_KEY')
        self.service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'iqstrade-notifications-firebase-adminsdk-fbsvc-f52d11527b.json')
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
        
        # Try to get server key from service account if not provided
        if not self.server_key:
            self.server_key = self._get_server_key_from_service_account()
        
        if not self.server_key:
            print("⚠️ Warning: FIREBASE_SERVER_KEY not found and could not be extracted from service account")
    
    def _get_server_key_from_service_account(self):
        """Try to extract server key from service account JSON"""
        try:
            if os.path.exists(self.service_account_path):
                with open(self.service_account_path, 'r') as f:
                    service_account = json.load(f)
                
                # The service account doesn't contain server key directly
                # We need to use a different approach
                print("ℹ️ Service account found, but server key needs to be obtained differently")
                return None
            else:
                print(f"ℹ️ Service account file not found: {self.service_account_path}")
                return None
        except Exception as e:
            print(f"❌ Error reading service account: {e}")
            return None
    
    def send_notification(self, tokens: List[str], title: str, body: str, data: Dict = None) -> Dict:
        """
        Send notification to specific FCM tokens
        """
        if not self.server_key:
            return {'success': False, 'error': 'FCM server key not configured'}
        
        if not tokens:
            return {'success': False, 'error': 'No tokens provided'}
        
        payload = {
            'registration_ids': tokens,
            'notification': {
                'title': title,
                'body': body,
                'icon': '/favicon.ico',
                'badge': '1',
                'requireInteraction': True
            },
            'data': data or {},
            'priority': 'high',
            'content_available': True
        }
        
        headers = {
            'Authorization': f'key={self.server_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(self.fcm_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            success_count = result.get('success', 0)
            failure_count = result.get('failure', 0)
            
            return {
                'success': True,
                'response': result,
                'success_count': success_count,
                'failure_count': failure_count,
                'total_sent': len(tokens)
            }
            
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def send_to_topic(self, topic: str, title: str, body: str, data: Dict = None) -> Dict:
        """
        Send notification to a topic (all subscribed devices)
        """
        if not self.server_key:
            return {'success': False, 'error': 'FCM server key not configured'}
        
        payload = {
            'to': f'/topics/{topic}',
            'notification': {
                'title': title,
                'body': body,
                'icon': '/favicon.ico',
                'badge': '1',
                'requireInteraction': True
            },
            'data': data or {},
            'priority': 'high',
            'content_available': True
        }
        
        headers = {
            'Authorization': f'key={self.server_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(self.fcm_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return {
                'success': True,
                'response': result,
                'topic': topic
            }
            
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    # High Priority Notification Methods
    
    def send_new_bill_notification(self, bill_id: int, customer_name: str, amount: float, bill_number: str) -> Dict:
        """
        Send notification for new bill upload
        """
        title = "🔔 New Bill of Lading Received"
        body = f"Order #{bill_number} uploaded by {customer_name}"
        
        data = {
            'type': 'new_bill',
            'billId': str(bill_id),
            'billNumber': bill_number,
            'customerName': customer_name,
            'amount': str(amount),
            'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
        }
        
        return self.send_to_topic('new_bills', title, body, data)
    
    def send_payment_confirmation_notification(self, bill_id: int, bill_number: str, amount: float, payment_method: str) -> Dict:
        """
        Send notification for payment confirmation
        """
        title = "✅ Payment Confirmed"
        body = f"Payment received for #{bill_number} - ${amount:,.2f}"
        
        data = {
            'type': 'payment_confirmation',
            'billId': str(bill_id),
            'billNumber': bill_number,
            'amount': str(amount),
            'paymentMethod': payment_method,
            'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
        }
        
        return self.send_to_topic('payment_confirmations', title, body, data)
    
    def send_system_error_notification(self, error_type: str, error_message: str, severity: str = 'high') -> Dict:
        """
        Send notification for system errors
        """
        title = f"🚨 System Alert - {error_type.title()}"
        body = f"System error detected: {error_message}"
        
        data = {
            'type': 'system_error',
            'errorType': error_type,
            'errorMessage': error_message,
            'severity': severity,
            'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
        }
        
        return self.send_to_topic('system_alerts', title, body, data)
    
    def send_customer_escalation_notification(self, customer_name: str, customer_phone: str, issue_type: str, priority: str = 'high') -> Dict:
        """
        Send notification for customer escalations
        """
        title = "📞 Customer Escalation"
        body = f"Escalation from {customer_name} - {issue_type}"
        
        data = {
            'type': 'customer_escalation',
            'customerName': customer_name,
            'customerPhone': customer_phone,
            'issueType': issue_type,
            'priority': priority,
            'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
        }
        
        return self.send_to_topic('customer_escalations', title, body, data)

# Global FCM service instance
fcm_service = FCMService() 