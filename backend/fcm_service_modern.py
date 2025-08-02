import os
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import pytz
from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import service_account

class FCMService:
    def __init__(self):
        self.fcm_url = 'https://fcm.googleapis.com/v1/projects/iqstrade-notifications/messages:send'
        self.service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'iqstrade-notifications-firebase-adminsdk-fbsvc-f52d11527b.json')
        self.project_id = 'iqstrade-notifications'
        self.credentials = None
        self.access_token = None
        
        # Initialize credentials
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        """Initialize Google credentials for FCM"""
        try:
            # Try to use service account file
            if os.path.exists(self.service_account_path):
                self.credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_path,
                    scopes=['https://www.googleapis.com/auth/firebase.messaging']
                )
                print(f"✅ Service account credentials loaded from: {self.service_account_path}")
            else:
                # Try to use default credentials (for Google Cloud environments)
                self.credentials, _ = default(scopes=['https://www.googleapis.com/auth/firebase.messaging'])
                print("✅ Using default Google Cloud credentials")
            
            # Get initial access token
            self._refresh_access_token()
            
        except Exception as e:
            print(f"❌ Error initializing credentials: {e}")
            self.credentials = None
    
    def _refresh_access_token(self):
        """Refresh the OAuth 2.0 access token"""
        try:
            if self.credentials:
                self.credentials.refresh(Request())
                self.access_token = self.credentials.token
                print(f"✅ Access token refreshed: {self.access_token[:20]}...")
            else:
                print("❌ No credentials available")
        except Exception as e:
            print(f"❌ Error refreshing access token: {e}")
    
    def _get_valid_access_token(self):
        """Get a valid access token, refreshing if necessary"""
        if not self.credentials:
            return None
        
        # Check if token is expired or about to expire
        if not self.access_token or self.credentials.expired:
            self._refresh_access_token()
        
        return self.access_token
    
    def send_notification(self, tokens: List[str], title: str, body: str, data: Dict = None) -> Dict:
        """
        Send notification to specific FCM tokens using HTTP v1 API with server key
        """
        server_key = os.getenv('FIREBASE_SERVER_KEY')
        if not server_key:
            return {'success': False, 'error': 'FIREBASE_SERVER_KEY not found in environment variables'}
        
        if not tokens:
            return {'success': False, 'error': 'No tokens provided'}
        
        # HTTP v1 API format with server key
        headers = {
            'Authorization': f'key={server_key}',
            'Content-Type': 'application/json'
        }
        
        results = []
        for i, token in enumerate(tokens):
            try:
                # HTTP v1 API format
                message = {
                    'message': {
                        'token': token,
                        'notification': {
                            'title': title,
                            'body': body
                        },
                        'data': {k: str(v) for k, v in (data or {}).items()},
                        'android': {
                            'priority': 'high',
                            'notification': {
                                'icon': '/favicon.ico',
                                'color': '#4285f4'
                            }
                        },
                        'webpush': {
                            'headers': {
                                'Urgency': 'high'
                            },
                            'notification': {
                                'icon': '/favicon.ico',
                                'badge': '/favicon.ico',
                                'requireInteraction': True
                            }
                        }
                    }
                }
                
                print(f'📱 Sending message {i+1}/{len(tokens)} to FCM...')
                print(f'📱 FCM URL: {self.fcm_url}')
                print(f'📱 Headers: {headers}')
                print(f'📱 Message: {json.dumps(message, indent=2)}')
                
                response = requests.post(self.fcm_url, json=message, headers=headers)
                print(f'📱 FCM Response Status: {response.status_code}')
                print(f'📱 FCM Response Headers: {dict(response.headers)}')
                print(f'📱 FCM Response Text: {response.text}')
                
                response.raise_for_status()
                
                result = response.json()
                results.append({
                    'success': True,
                    'response': result
                })
                print(f'📱 Message {i+1} sent successfully')
                
            except requests.exceptions.RequestException as e:
                print(f'📱 Message {i+1} failed: {e}')
                results.append({
                    'success': False,
                    'error': str(e)
                })
        
        success_count = sum(1 for r in results if r['success'])
        failure_count = len(results) - success_count
        
        return {
            'success': success_count > 0,
            'results': results,
            'success_count': success_count,
            'failure_count': failure_count,
            'total_sent': len(tokens)
        }
    
    def send_to_topic(self, topic: str, title: str, body: str, data: Dict = None) -> Dict:
        """
        Send notification to a topic using HTTP v1 API with server key
        """
        server_key = os.getenv('FIREBASE_SERVER_KEY')
        if not server_key:
            return {'success': False, 'error': 'FIREBASE_SERVER_KEY not found in environment variables'}
        
        # HTTP v1 API format for topics
        message = {
            'message': {
                'topic': topic,
                'notification': {
                    'title': title,
                    'body': body
                },
                'data': {k: str(v) for k, v in (data or {}).items()},
                'android': {
                    'priority': 'high',
                    'notification': {
                        'icon': '/favicon.ico',
                        'color': '#4285f4'
                    }
                },
                'webpush': {
                    'headers': {
                        'Urgency': 'high'
                    },
                    'notification': {
                        'icon': '/favicon.ico',
                        'badge': '/favicon.ico',
                        'requireInteraction': True
                    }
                }
            }
        }
        
        headers = {
            'Authorization': f'key={server_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(self.fcm_url, json=message, headers=headers)
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
    
    def subscribe_to_topic(self, token: str, topic: str) -> Dict:
        """
        Subscribe a token to a topic using FCM Legacy HTTP API
        """
        try:
            # Use FCM Legacy HTTP API for topic subscription
            subscription_url = f'https://iid.googleapis.com/iid/v1/{token}/rel/topics/{topic}'
            
            # Get server key from environment
            server_key = os.getenv('FIREBASE_SERVER_KEY')
            if not server_key:
                return {'success': False, 'error': 'FIREBASE_SERVER_KEY not found in environment variables'}
            
            headers = {
                'Authorization': f'key={server_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(subscription_url, headers=headers)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f'Successfully subscribed to topic: {topic}',
                    'token': token[:20] + '...',
                    'topic': topic
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to subscribe: {response.status_code} - {response.text}'
                }
                
        except Exception as e:
            return {'success': False, 'error': f'Error subscribing to topic: {str(e)}'}

# Global FCM service instance
fcm_service = FCMService() 