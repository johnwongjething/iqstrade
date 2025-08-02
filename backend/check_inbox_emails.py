#!/usr/bin/env python3
"""
Check emails in inbox to see if complex emails were received
"""

import imaplib
import email
import os
from email.header import decode_header
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(env_file)

def check_inbox_emails():
    """Check emails in inbox"""
    
    # Email configuration
    email_user = os.getenv('EMAIL_USERNAME')
    email_password = os.getenv('EMAIL_PASSWORD')
    email_host = os.getenv('EMAIL_HOST')
    
    print("🔍 Checking Inbox Emails")
    print("=" * 50)
    print(f"📧 Email: {email_user}")
    print(f"📧 Host: {email_host}")
    print("=" * 50)
    
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(email_host, 993)
        mail.login(email_user, email_password)
        
        # Select inbox
        mail.select('INBOX')
        
        # Search for recent emails (last 24 hours)
        status, messages = mail.search(None, 'SINCE "29-Jul-2025"')
        
        if status != 'OK':
            print("❌ Failed to search emails")
            return
        
        email_ids = messages[0].split()
        
        if not email_ids:
            print("❌ No emails found in the last 24 hours")
            return
        
        print(f"📊 Found {len(email_ids)} emails in the last 24 hours")
        print("\n📧 Recent emails:")
        print("-" * 50)
        
        # Get the last 10 emails
        for i, email_id in enumerate(email_ids[-10:], 1):
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Get subject
                subject = decode_header(email_message["subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Get sender
                sender = email_message["from"]
                
                # Get date
                date = email_message["date"]
                
                print(f"{i}. Subject: {subject}")
                print(f"   From: {sender}")
                print(f"   Date: {date}")
                print()
                
            except Exception as e:
                print(f"❌ Error reading email {i}: {e}")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"❌ Failed to connect to email: {e}")

def check_sent_emails():
    """Check sent emails to see if they were actually sent"""
    
    # Email configuration
    email_user = os.getenv('EMAIL_USERNAME')
    email_password = os.getenv('EMAIL_PASSWORD')
    email_host = os.getenv('EMAIL_HOST')
    
    print("\n🔍 Checking Sent Emails")
    print("=" * 50)
    
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(email_host, 993)
        mail.login(email_user, email_password)
        
        # Select sent folder
        mail.select('"[Gmail]/Sent Mail"')
        
        # Search for recent sent emails
        status, messages = mail.search(None, 'SINCE "29-Jul-2025"')
        
        if status != 'OK':
            print("❌ Failed to search sent emails")
            return
        
        email_ids = messages[0].split()
        
        if not email_ids:
            print("❌ No sent emails found in the last 24 hours")
            return
        
        print(f"📊 Found {len(email_ids)} sent emails in the last 24 hours")
        print("\n📧 Recent sent emails:")
        print("-" * 50)
        
        # Get the last 5 sent emails
        for i, email_id in enumerate(email_ids[-5:], 1):
            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Get subject
                subject = decode_header(email_message["subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Get recipient
                recipient = email_message["to"]
                
                # Get date
                date = email_message["date"]
                
                print(f"{i}. Subject: {subject}")
                print(f"   To: {recipient}")
                print(f"   Date: {date}")
                print()
                
            except Exception as e:
                print(f"❌ Error reading sent email {i}: {e}")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"❌ Failed to check sent emails: {e}")

def main():
    """Main function"""
    print("📧 Email Inbox Checker")
    print("=" * 30)
    
    check_inbox_emails()
    check_sent_emails()
    
    print("\n📋 Summary:")
    print("1. Check if complex emails are in your inbox")
    print("2. Check if they were actually sent")
    print("3. If not found, the SMTP sending failed")

if __name__ == "__main__":
    main() 