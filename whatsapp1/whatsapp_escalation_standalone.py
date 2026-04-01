#!/usr/bin/env python3
"""
WhatsApp Escalation Handler - Standalone Version
Copy this file to your WhatsApp bot folder and integrate it.

Handles "live chat" requests and notifies the team when customers need human assistance.
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Optional
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppEscalationHandler:
    """
    Handles WhatsApp escalation requests when customers type "live chat"
    """
    
    def __init__(self):
        """Initialize the escalation handler"""
        self.escalation_keywords = [
            'live chat',
            'human',
            'speak to someone',
            'talk to someone',
            'real person',
            'agent',
            'representative',
            'customer service',
            'support',
            'help me',
            '人工',
            '客服',
            '人工客服',
            '真人',
            '接线员'
        ]
        
        # Email configuration for team notifications
        # Update these with your actual email settings
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp-relay.brevo.com')
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL')
        self.team_email = os.getenv('TEAM_EMAIL', self.from_email)
        
    def is_escalation_request(self, message: str) -> bool:
        """
        Check if the message is requesting live chat escalation
        
        Args:
            message: Customer message
            
        Returns:
            bool: True if escalation is requested
        """
        message_lower = message.lower().strip()
        
        # Check for exact "live chat" match first
        if message_lower == 'live chat':
            return True
            
        # Check for other escalation keywords
        for keyword in self.escalation_keywords:
            if keyword in message_lower:
                return True
                
        return False
    
    def get_escalation_response(self, customer_name: str = None, customer_phone: str = None) -> str:
        """
        Generate response to customer when escalation is triggered
        
        Args:
            customer_name: Customer's name (if available)
            customer_phone: Customer's phone number
            
        Returns:
            str: Response message to customer
        """
        name_part = f" {customer_name}" if customer_name else ""
        
        response = f"""Hi{name_part}! 👋

I understand you'd like to speak with a human representative. 

✅ **Your request has been escalated to our team**
📞 **We'll contact you within 5-10 minutes**

**What happens next:**
• Our team will review your conversation history
• They'll call you on this WhatsApp number
• They'll have full context of your enquiry

**In the meantime, you can also:**
📧 Email: info@iqstrade.com
📱 Phone: +852 XXXX XXXX
🏢 Office: [Your office address]

Thank you for your patience! 🙏"""
        
        return response
    
    def notify_team(self, customer_data: Dict, conversation_history: list = None) -> bool:
        """
        Send notification email to the team about escalation
        
        Args:
            customer_data: Dictionary with customer information
            conversation_history: List of recent messages
            
        Returns:
            bool: True if notification sent successfully
        """
        try:
            # Prepare email content
            subject = f"🚨 WhatsApp Escalation Request - {customer_data.get('name', 'Unknown Customer')}"
            
            # Build email body
            body = self._build_notification_email(customer_data, conversation_history)
            
            # Send email
            success = self._send_email(subject, body)
            
            if success:
                logger.info(f"✅ Team notification sent for escalation from {customer_data.get('phone', 'Unknown')}")
            else:
                logger.error(f"❌ Failed to send team notification for escalation")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending team notification: {e}")
            return False
    
    def _build_notification_email(self, customer_data: Dict, conversation_history: list = None) -> str:
        """
        Build the notification email content
        
        Args:
            customer_data: Customer information
            conversation_history: Recent conversation messages
            
        Returns:
            str: Formatted email body
        """
        customer_name = customer_data.get('name', 'Unknown Customer')
        customer_phone = customer_data.get('phone', 'Unknown')
        escalation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        email_body = f"""
🚨 **WHATSAPP ESCALATION REQUEST**

**Customer Details:**
• Name: {customer_name}
• Phone: {customer_phone}
• Time: {escalation_time}

**Action Required:**
Please call this customer within 5-10 minutes to provide human assistance.

**Recent Conversation:**
"""
        
        if conversation_history:
            for i, msg in enumerate(conversation_history[-5:], 1):  # Last 5 messages
                sender = "Customer" if msg.get('from_customer', True) else "Bot"
                timestamp = msg.get('timestamp', 'Unknown time')
                content = msg.get('content', 'No content')
                
                email_body += f"""
{i}. **{sender}** ({timestamp}):
{content}
"""
        else:
            email_body += "No conversation history available."
        
        email_body += f"""

**Quick Actions:**
📞 Call: {customer_phone}
📧 Email: {customer_data.get('email', 'No email provided')}
🔗 WhatsApp: https://wa.me/{customer_phone.replace('+', '')}

**System Info:**
• Escalation triggered by: "live chat" request
• Bot was unable to satisfy customer needs
• Customer explicitly requested human assistance

Please respond promptly to maintain customer satisfaction! 🙏
"""
        
        return email_body
    
    def _send_email(self, subject: str, body: str) -> bool:
        """
        Send email notification to the team
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            if not all([self.smtp_server, self.smtp_username, self.smtp_password, self.from_email, self.team_email]):
                logger.error("❌ Missing email configuration for team notifications")
                logger.error("Please set these environment variables:")
                logger.error("SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL, TEAM_EMAIL")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.team_email
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, 587) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return False
    
    def log_escalation(self, customer_data: Dict, conversation_history: list = None) -> None:
        """
        Log escalation request to console (you can extend this to save to file/database)
        
        Args:
            customer_data: Customer information
            conversation_history: Recent conversation messages
        """
        try:
            escalation_log = {
                'timestamp': datetime.now().isoformat(),
                'customer_data': customer_data,
                'conversation_history': conversation_history,
                'status': 'pending'
            }
            
            # Log to console
            logger.info(f"📝 Escalation logged for {customer_data.get('phone', 'Unknown')}")
            logger.info(f"📝 Escalation details: {json.dumps(escalation_log, indent=2)}")
            
            # You can extend this to save to a file or database
            # with open('escalations.log', 'a') as f:
            #     f.write(json.dumps(escalation_log) + '\n')
            
        except Exception as e:
            logger.error(f"❌ Error logging escalation: {e}")

# Global instance
escalation_handler = WhatsAppEscalationHandler()

def handle_whatsapp_message(message: str, customer_data: Dict, conversation_history: list = None) -> Dict:
    """
    Main function to handle WhatsApp messages and check for escalation
    
    Args:
        message: Customer message
        customer_data: Customer information (name, phone, email)
        conversation_history: Recent conversation messages
        
    Returns:
        Dict with 'escalation_requested', 'response', and 'notify_team'
    """
    try:
        # Check if this is an escalation request
        is_escalation = escalation_handler.is_escalation_request(message)
        
        if is_escalation:
            # Generate escalation response
            response = escalation_handler.get_escalation_response(
                customer_data.get('name'),
                customer_data.get('phone')
            )
            
            # Notify team
            team_notified = escalation_handler.notify_team(customer_data, conversation_history)
            
            # Log escalation
            escalation_handler.log_escalation(customer_data, conversation_history)
            
            return {
                'escalation_requested': True,
                'response': response,
                'notify_team': team_notified,
                'customer_data': customer_data
            }
        else:
            # Not an escalation request, continue with normal bot processing
            return {
                'escalation_requested': False,
                'response': None,
                'notify_team': False
            }
            
    except Exception as e:
        logger.error(f"❌ Error in WhatsApp escalation handler: {e}")
        return {
            'escalation_requested': False,
            'response': None,
            'notify_team': False,
            'error': str(e)
        }

# Test function
def test_escalation():
    """Test the escalation functionality"""
    print("🧪 Testing WhatsApp Escalation Handler")
    print("=" * 50)
    
    # Test escalation detection
    test_messages = [
        "live chat",
        "I want to speak to a human",
        "Can I talk to someone?",
        "人工客服",
        "Hello, how are you?",
        "What's the status of my shipment?"
    ]
    
    for msg in test_messages:
        is_escalation = escalation_handler.is_escalation_request(msg)
        print(f"'{msg}' -> Escalation: {is_escalation}")
    
    # Test escalation response
    customer_data = {
        'name': 'John Doe',
        'phone': '+852 1234 5678',
        'email': 'john@example.com'
    }
    
    response = escalation_handler.get_escalation_response(
        customer_data['name'],
        customer_data['phone']
    )
    
    print(f"\n📧 Escalation Response:")
    print(response)
    
    print(f"\n✅ Test completed!")
    print(f"\n📝 Next steps:")
    print(f"1. Copy this file to your WhatsApp bot folder")
    print(f"2. Set up environment variables (SMTP_SERVER, SMTP_USERNAME, etc.)")
    print(f"3. Integrate the handle_whatsapp_message function into your bot")
    print(f"4. Test with real WhatsApp messages")

if __name__ == "__main__":
    test_escalation() 