import os
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import pytz

class FCMService:
    def __init__(self):
        self.server_key = os.getenv('FIREBASE_SERVER_KEY')
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
        
        if not self.server_key:
            print("⚠️ Warning: FIREBASE_SERVER_KEY not found in environment variables")
    
    def send_notification(self, tokens: List[str], title: str, body: str, data: Dict = None) -> Dict:
        """
        Send notification to specific FCM tokens
        
        Args:
            tokens: List of FCM tokens
            title: Notification title
            body: Notification body
            data: Additional data to send with notification
            
        Returns:
            Dict with success status and response
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
        
        Args:
            topic: Topic name (e.g., 'new_bills', 'system_alerts')
            title: Notification title
            body: Notification body
            data: Additional data to send with notification
            
        Returns:
            Dict with success status and response
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
    
    def send_to_specific_users(self, user_ids: List[int], title: str, body: str, data: Dict = None) -> Dict:
        """
        Send notification to specific users by their user IDs
        This method will fetch FCM tokens for the given user IDs and send notifications
        """
        # This would need to be implemented with database integration
        # For now, return a placeholder
        return {
            'success': False, 
            'error': 'User-specific notifications not yet implemented. Use send_notification with tokens instead.'
        }

# Global FCM service instance
fcm_service = FCMService()

# Backward compatibility functions
def send_fcm_notification(tokens: List[str], title: str, body: str, data: Dict = None) -> Dict:
    """
    Send FCM notification to specific tokens (backward compatibility function)
    """
    return fcm_service.send_notification(tokens, title, body, data)

def send_fcm_notification_to_topic(topic: str, title: str, body: str, data: Dict = None) -> Dict:
    """
    Send FCM notification to a topic (backward compatibility function)
    """
    return fcm_service.send_to_topic(topic, title, body, data)

def send_payment_notification(bill_id: int, bill_number: str, amount: float, payment_method: str) -> Dict:
    """
    Send payment confirmation notification (backward compatibility function)
    """
    return fcm_service.send_payment_confirmation_notification(bill_id, bill_number, amount, payment_method)

def send_new_bill_notification(bill_id: int, customer_name: str, amount: float, bill_number: str) -> Dict:
    """
    Send new bill notification (backward compatibility function)
    """
    return fcm_service.send_new_bill_notification(bill_id, customer_name, amount, bill_number) 