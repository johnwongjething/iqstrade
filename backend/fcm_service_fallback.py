import os
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import pytz
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.auth import default

class FCMServiceFallback:
    """
    FCM Service with automatic fallback between modern HTTP v1 API and legacy API
    """
    
    def __init__(self):
        self.project_id = 'iqstrade-notifications'
        self.fcm_url = f'https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send'
        
        # Modern API credentials
        self.service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        self.credentials = None
        self.access_token = None
        
        # Initialize modern API
        self._initialize_modern_api()
        
        print(f"🔔 FCM Service initialized:")
        print(f"   Modern API: {'✅' if self.credentials else '❌'}")
        if not self.credentials:
            print(f"   ⚠️ Service account not configured: {self.service_account_path}")
    
    def _initialize_modern_api(self):
        """Initialize modern HTTP v1 API credentials"""
        try:
            # Try to use service account file first
            if self.service_account_path and os.path.exists(self.service_account_path):
                try:
                    self.credentials = service_account.Credentials.from_service_account_file(
                        self.service_account_path,
                        scopes=['https://www.googleapis.com/auth/firebase.messaging']
                    )
                    print(f"✅ Modern API credentials loaded from: {self.service_account_path}")
                except Exception as sa_error:
                    print(f"❌ Service account file error: {sa_error}")
                    # Try to read and validate the file content
                    try:
                        import json
                        with open(self.service_account_path, 'r') as f:
                            content = json.load(f)
                        print(f"📄 Service account file contains: {list(content.keys())}")
                        if 'private_key' in content:
                            print(f"🔑 Private key length: {len(content['private_key'])} characters")
                        else:
                            print("❌ No private_key found in service account file")
                    except Exception as read_error:
                        print(f"❌ Cannot read service account file: {read_error}")
                    self.credentials = None
                    return
            else:
                print(f"⚠️ Service account file not found: {self.service_account_path}")
                self.credentials = None
                return
            
            # Get initial access token
            if self.credentials:
                self._refresh_access_token()
            
        except Exception as e:
            print(f"❌ Failed to initialize modern API: {e}")
            self.credentials = None
    
    def _refresh_access_token(self):
        """Refresh the OAuth 2.0 access token"""
        try:
            if self.credentials:
                self.credentials.refresh(Request())
                self.access_token = self.credentials.token
                print(f"✅ Access token refreshed: {self.access_token[:20]}...")
        except Exception as e:
            print(f"❌ Error refreshing access token: {e}")
            self.access_token = None
    
    def _get_valid_access_token(self):
        """Get a valid access token, refreshing if necessary"""
        if not self.credentials:
            return None
        
        if not self.access_token or self.credentials.expired:
            self._refresh_access_token()
        
        return self.access_token
    
    def send_notification(self, tokens: List[str], title: str, body: str, data: Dict = None) -> Dict:
        """
        Send notification using modern API only (legacy API is deprecated)
        """
        if not tokens:
            return {'success': False, 'error': 'No tokens provided'}
        
        # Use modern API only
        if self.credentials:
            return self._send_modern_notification(tokens, title, body, data)
        else:
            return {'success': False, 'error': 'No FCM credentials available - service account not configured'}
    
    def _send_modern_notification(self, tokens: List[str], title: str, body: str, data: Dict = None) -> Dict:
        """Send notification using modern HTTP v1 API"""
        access_token = self._get_valid_access_token()
        if not access_token:
            return {'success': False, 'error': 'Failed to get valid access token'}
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        results = []
        for i, token in enumerate(tokens):
            try:
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
                
                print(f'📱 [Modern API] Sending message {i+1}/{len(tokens)}...')
                response = requests.post(self.fcm_url, json=message, headers=headers)
                
                if response.status_code == 200:
                    results.append({'success': True, 'response': response.json()})
                    print(f'📱 [Modern API] Message {i+1} sent successfully')
                else:
                    print(f'📱 [Modern API] Message {i+1} failed: {response.status_code} - {response.text}')
                    results.append({'success': False, 'error': f'HTTP {response.status_code}: {response.text}'})
                    
            except Exception as e:
                print(f'📱 [Modern API] Message {i+1} failed: {e}')
                results.append({'success': False, 'error': str(e)})
        
        success_count = sum(1 for r in results if r['success'])
        return {
            'success': success_count > 0,
            'results': results,
            'success_count': success_count,
            'failure_count': len(results) - success_count,
            'total_sent': len(tokens),
            'api_used': 'modern'
        }
    
    def _send_modern_topic_notification(self, topic: str, title: str, body: str, data: Dict = None) -> Dict:
        """Send topic notification using modern API"""
        access_token = self._get_valid_access_token()
        if not access_token:
            return {'success': False, 'error': 'Failed to get valid access token'}
        
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
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            print(f'📱 [Modern API] Sending topic notification to "{topic}"...')
            response = requests.post(self.fcm_url, json=message, headers=headers)
            response.raise_for_status()
            
            return {
                'success': True,
                'response': response.json(),
                'api_used': 'modern'
            }
            
        except requests.exceptions.RequestException as e:
            print(f'📱 [Modern API] Topic notification failed: {e}')
            return {'success': False, 'error': str(e), 'api_used': 'modern'}
    
    def send_to_topic(self, topic: str, title: str, body: str, data: Dict = None) -> Dict:
        """
        Send notification to a topic using modern API only
        """
        if self.credentials:
            return self._send_modern_topic_notification(topic, title, body, data)
        else:
            return {'success': False, 'error': 'No FCM credentials available for topic notifications'}

# Create global instance
fcm_service_fallback = FCMServiceFallback() 