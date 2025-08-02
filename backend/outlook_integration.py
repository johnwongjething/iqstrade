#!/usr/bin/env python3
"""
Microsoft Outlook Integration
Send AI-generated replies directly to customers via SMTP
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import logging
from config import get_db_conn

logger = logging.getLogger(__name__)

class OutlookIntegration:
    """
    Integrate with Microsoft Outlook via SMTP
    Send AI-generated replies directly to customers
    """
    
    def __init__(self):
        # SMTP Configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp-mail.outlook.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.from_name = os.getenv('FROM_NAME', 'IQS Trade Support')
        
        # Validate configuration
        if not all([self.smtp_username, self.smtp_password]):
            logger.error("❌ SMTP configuration missing. Please set SMTP_USERNAME and SMTP_PASSWORD")
    
    def send_email_reply(self, customer_email_id, reply_text, subject=None, attachments=None):
        """
        Send AI-generated reply to customer via SMTP
        
        Args:
            customer_email_id: ID of the original customer email
            reply_text: AI-generated reply text
            subject: Email subject (optional, will use original if not provided)
            attachments: List of attachment file paths (optional)
        
        Returns:
            dict: Result with success status and message
        """
        
        try:
            # Get customer email details
            customer_email = self._get_customer_email(customer_email_id)
            if not customer_email:
                return {"success": False, "error": "Customer email not found"}
            
            # Prepare email
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = customer_email['sender']
            msg['Subject'] = subject or f"Re: {customer_email['subject']}"
            
            # Add reply text
            msg.attach(MIMEText(reply_text, 'plain'))
            
            # Add attachments if provided
            if attachments:
                for attachment_path in attachments:
                    self._add_attachment(msg, attachment_path)
            
            # Send email
            self._send_smtp_email(msg)
            
            # Update database
            self._update_email_sent_status(customer_email_id, reply_text)
            
            logger.info(f"✅ Email sent successfully to {customer_email['sender']}")
            return {"success": True, "message": "Email sent successfully"}
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_customer_email(self, customer_email_id):
        """Get customer email details from database"""
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sender, subject, body, created_at
                FROM customer_emails 
                WHERE id = %s
            """, (customer_email_id,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return {
                    'sender': result[0],
                    'subject': result[1],
                    'body': result[2],
                    'created_at': result[3]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting customer email: {e}")
            return None
    
    def _add_attachment(self, msg, file_path):
        """Add attachment to email"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(file_path)}'
            )
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Error adding attachment {file_path}: {e}")
    
    def _send_smtp_email(self, msg):
        """Send email via SMTP"""
        try:
            # Create secure SSL/TLS connection
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise e
    
    def _update_email_sent_status(self, customer_email_id, reply_text):
        """Update database to mark email as sent"""
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            
            # Update the reply record
            cursor.execute("""
                UPDATE customer_email_replies 
                SET sent_at = %s, sent_via = 'smtp', auto_sent = true, auto_sent_at = %s
                WHERE customer_email_id = %s AND body = %s
                ORDER BY created_at DESC
                LIMIT 1
            """, (datetime.now(), datetime.now(), customer_email_id, reply_text))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating sent status: {e}")
    
    def auto_send_high_confidence_replies(self):
        """
        Automatically send high-confidence AI replies
        This can be run as a scheduled task
        """
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            
            # Get high-confidence replies that haven't been sent
            cursor.execute("""
                SELECT 
                    cer.id,
                    cer.customer_email_id,
                    cer.body,
                    cer.confidence_score,
                    ce.sender,
                    ce.subject
                FROM customer_email_replies cer
                JOIN customer_emails ce ON cer.customer_email_id = ce.id
                WHERE cer.auto_send_recommended = true 
                    AND cer.auto_sent = false
                    AND cer.confidence_score >= 0.8
                ORDER BY cer.created_at DESC
            """)
            
            replies = cursor.fetchall()
            cursor.close()
            conn.close()
            
            logger.info(f"Found {len(replies)} high-confidence replies to send")
            
            sent_count = 0
            for reply in replies:
                reply_id, customer_email_id, body, confidence, sender, subject = reply
                
                result = self.send_email_reply(
                    customer_email_id=customer_email_id,
                    reply_text=body,
                    subject=f"Re: {subject}"
                )
                
                if result['success']:
                    sent_count += 1
                    logger.info(f"✅ Auto-sent reply {reply_id} to {sender} (confidence: {confidence})")
                else:
                    logger.error(f"❌ Failed to send reply {reply_id}: {result['error']}")
            
            logger.info(f"Auto-send complete: {sent_count}/{len(replies)} emails sent")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error in auto-send: {e}")
            return 0

def setup_outlook_config():
    """Setup Outlook configuration in .env.local"""
    
    config_template = """
# Microsoft Outlook SMTP Configuration
# Add these to your .env.local file:

# SMTP Settings
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your_email@outlook.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@outlook.com
FROM_NAME=IQS Trade Support

# Note: For Outlook, you may need to:
# 1. Enable 2-factor authentication
# 2. Generate an "App Password" for SMTP access
# 3. Use the app password instead of your regular password
"""
    
    print("🔧 Outlook Integration Setup")
    print("=" * 40)
    print(config_template)
    
    # Check if config exists
    env_file = ".env.local"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            content = f.read()
        
        if 'SMTP_USERNAME' in content:
            print("✅ SMTP configuration already exists in .env.local")
        else:
            print("⚠️ Add the SMTP configuration to your .env.local file")
    else:
        print("⚠️ Create .env.local file with SMTP configuration")

if __name__ == "__main__":
    print("🔧 Microsoft Outlook Integration")
    print("=" * 40)
    
    # Setup configuration
    setup_outlook_config()
    
    # Test integration if configured
    integration = OutlookIntegration()
    
    if integration.smtp_username and integration.smtp_password:
        print("\n🧪 Testing Outlook Integration...")
        
        # Test with a sample email
        test_result = integration.send_email_reply(
            customer_email_id=1,  # Replace with actual email ID
            reply_text="This is a test reply from the Outlook integration system.",
            subject="Test Reply"
        )
        
        print(f"Test Result: {test_result}")
    else:
        print("\n❌ SMTP configuration not found. Please configure first.") 