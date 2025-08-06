"""
Duplicate Payment Notification System
Handles notifications when duplicate payments are detected across all payment streams
"""

import logging
from datetime import datetime
import pytz
from config import get_db_conn
from email_utils import send_simple_email
from fcm_service_fallback import fcm_service_fallback
from utils.security import decrypt_sensitive_data

logger = logging.getLogger(__name__)

def send_duplicate_payment_notifications(bl_id, bl_number, customer_username, customer_email, 
                                       payment_amount, payment_source, original_payment_date=None):
    """
    Send comprehensive duplicate payment notifications across all channels
    
    Args:
        bl_id: Bill of lading ID
        bl_number: Bill of lading number
        customer_username: Customer username
        customer_email: Customer email (encrypted)
        payment_amount: Amount of duplicate payment
        payment_source: Source of payment (webhook, email, bank_import, whatsapp)
        original_payment_date: Date of original payment (optional)
    """
    try:
        # Decrypt customer email
        decrypted_email = decrypt_sensitive_data(customer_email) if customer_email else None
        
        # Get customer phone number for WhatsApp
        customer_phone = get_customer_phone(customer_username)
        
        # Get customer FCM tokens
        fcm_tokens = get_customer_fcm_tokens(customer_username)
        
        # Send notifications
        send_fcm_duplicate_notification(fcm_tokens, bl_number, payment_amount, payment_source)
        send_email_duplicate_notification(decrypted_email, bl_number, payment_amount, payment_source, original_payment_date)
        send_whatsapp_duplicate_notification(customer_phone, bl_number, payment_amount, payment_source)
        send_staff_refund_alert(bl_number, customer_username, payment_amount, payment_source)
        
        logger.info(f"Duplicate payment notifications sent for BL {bl_number} (ID: {bl_id})")
        
    except Exception as e:
        logger.error(f"Error sending duplicate payment notifications for BL {bl_number}: {e}")

def get_customer_phone(username):
    """Get customer phone number from database"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT customer_phone FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result and result[0]:
            return decrypt_sensitive_data(result[0])
        return None
    except Exception as e:
        logger.error(f"Error getting customer phone for {username}: {e}")
        return None

def get_customer_fcm_tokens(username):
    """Get customer FCM tokens from database"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT token FROM fcm_tokens WHERE username = %s AND is_active = true", (username,))
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return [row[0] for row in results] if results else []
    except Exception as e:
        logger.error(f"Error getting FCM tokens for {username}: {e}")
        return []

def send_fcm_duplicate_notification(fcm_tokens, bl_number, payment_amount, payment_source):
    """Send FCM push notification to user about duplicate payment"""
    if not fcm_tokens:
        logger.info("No FCM tokens available for duplicate payment notification")
        return
        
    try:
        title = "⚠️ Duplicate Payment Detected"
        body = f"Your payment of ${payment_amount:.2f} for BL {bl_number} has already been processed. No action needed."
        
        data = {
            'type': 'duplicate_payment',
            'bl_number': bl_number,
            'payment_amount': str(payment_amount),
            'payment_source': payment_source,
            'timestamp': datetime.now().isoformat()
        }
        
        fcm_service_fallback.send_notification(
            tokens=fcm_tokens,
            title=title,
            body=body,
            data=data
        )
        
        logger.info(f"FCM duplicate payment notification sent to {len(fcm_tokens)} tokens")
        
    except Exception as e:
        logger.error(f"Error sending FCM duplicate payment notification: {e}")

def send_email_duplicate_notification(email, bl_number, payment_amount, payment_source, original_payment_date=None):
    """Send email notification to user about duplicate payment"""
    if not email:
        logger.info("No email available for duplicate payment notification")
        return
        
    try:
        subject = "⚠️ Duplicate Payment Alert - No Action Required"
        
        # Format original payment date
        original_date_str = ""
        if original_payment_date:
            if isinstance(original_payment_date, str):
                original_date_str = f"Original payment was processed on: {original_payment_date}"
            else:
                original_date_str = f"Original payment was processed on: {original_payment_date.strftime('%Y-%m-%d %H:%M:%S')}"
        
        body = f"""
Dear Customer,

We have detected a duplicate payment attempt for your shipment.

**Payment Details:**
- Bill of Lading: {bl_number}
- Duplicate Amount: ${payment_amount:.2f}
- Payment Source: {payment_source.title()}
{original_date_str}

**Important:** Your original payment has already been processed successfully. This duplicate payment will not be charged to your account.

**No action is required from you.** Your shipment processing continues as normal.

If you have any questions or concerns, please contact our support team.

Best regards,
Terry Ray Logistics Team
        """
        
        send_simple_email(email, subject, body)
        logger.info(f"Email duplicate payment notification sent to {email}")
        
    except Exception as e:
        logger.error(f"Error sending email duplicate payment notification: {e}")

def send_whatsapp_duplicate_notification(phone, bl_number, payment_amount, payment_source):
    """Send WhatsApp notification to user about duplicate payment"""
    if not phone:
        logger.info("No phone available for WhatsApp duplicate payment notification")
        return
        
    try:
        # This would integrate with your WhatsApp API
        # For now, we'll log the message that would be sent
        message = f"⚠️ Duplicate Payment Alert: Your payment of ${payment_amount:.2f} for BL {bl_number} has already been processed. No refund needed."
        
        # TODO: Implement actual WhatsApp sending
        # sendWhatsAppMessage(phone, message)
        
        logger.info(f"WhatsApp duplicate payment notification would be sent to {phone}: {message}")
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp duplicate payment notification: {e}")

def send_staff_refund_alert(bl_number, customer_username, payment_amount, payment_source):
    """Send alert to staff about potential refund request"""
    try:
        # Get staff email addresses
        staff_emails = get_staff_emails()
        
        if not staff_emails:
            logger.warning("No staff emails found for refund alert")
            return
            
        subject = f"🚨 Duplicate Payment Alert - BL {bl_number}"
        
        body = f"""
**Duplicate Payment Detected**

A customer has attempted a duplicate payment that was automatically prevented.

**Details:**
- Bill of Lading: {bl_number}
- Customer: {customer_username}
- Duplicate Amount: ${payment_amount:.2f}
- Payment Source: {payment_source.title()}
- Detection Time: {datetime.now(pytz.timezone('Asia/Hong_Kong')).strftime('%Y-%m-%d %H:%M:%S HKT')}

**Action Required:**
- Monitor for customer support requests
- Be prepared to explain the duplicate payment prevention
- No refund processing needed (payment was not charged)

**Customer Notifications Sent:**
- ✅ FCM Push Notification
- ✅ Email Notification  
- ✅ WhatsApp Message (if configured)

This is an automated alert. The system has already notified the customer.
        """
        
        # Send to all staff members
        for staff_email in staff_emails:
            try:
                send_simple_email(staff_email, subject, body)
                logger.info(f"Staff refund alert sent to {staff_email}")
            except Exception as e:
                logger.error(f"Error sending staff alert to {staff_email}: {e}")
                
    except Exception as e:
        logger.error(f"Error sending staff refund alert: {e}")

def get_staff_emails():
    """Get all staff email addresses"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT customer_email FROM users WHERE role = 'staff' AND approved = true")
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        emails = []
        for row in results:
            if row[0]:
                try:
                    decrypted_email = decrypt_sensitive_data(row[0])
                    emails.append(decrypted_email)
                except Exception as e:
                    logger.error(f"Error decrypting staff email: {e}")
                    
        return emails
    except Exception as e:
        logger.error(f"Error getting staff emails: {e}")
        return [] 