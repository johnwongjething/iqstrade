#!/usr/bin/env python3
"""
Test IMAP Connection
"""

import os
import imaplib
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local')

print("🔍 Testing IMAP Connection")
print("=" * 40)

# Get email settings
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_USER = os.getenv('EMAIL_USERNAME')
EMAIL_PASS = os.getenv('EMAIL_PASSWORD')

print(f"📧 Email Host: {EMAIL_HOST}")
print(f"📧 Email User: {EMAIL_USER}")
print(f"📧 Email Pass: {'*' * len(EMAIL_PASS) if EMAIL_PASS else 'NOT SET'}")

if not all([EMAIL_HOST, EMAIL_USER, EMAIL_PASS]):
    print("❌ Missing email credentials")
    exit(1)

print(f"\n🔄 Attempting to connect to {EMAIL_HOST}...")

try:
    # Test connection
    mail = imaplib.IMAP4_SSL(EMAIL_HOST)
    print("✅ IMAP SSL connection successful")
    
    # Test login
    mail.login(EMAIL_USER, EMAIL_PASS)
    print("✅ Email login successful")
    
    # Test inbox selection
    mail.select('inbox')
    print("✅ Inbox selection successful")
    
    # Test search
    status, messages = mail.search(None, 'UNSEEN')
    if status == 'OK':
        email_count = len(messages[0].split())
        print(f"✅ Search successful - found {email_count} unread emails")
    else:
        print("❌ Search failed")
    
    mail.logout()
    print("✅ Logout successful")
    
except imaplib.IMAP4.error as e:
    print(f"❌ IMAP Error: {e}")
except ConnectionRefusedError as e:
    print(f"❌ Connection Refused: {e}")
    print("   This usually means:")
    print("   - Firewall blocking connection")
    print("   - Wrong port number")
    print("   - Server not accessible")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")

print("\n🎯 IMAP test completed!") 