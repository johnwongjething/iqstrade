#!/usr/bin/env python3
"""
Debug Duplicate Email Logic
"""
import os
import sys
import json
from config import get_db_conn

def check_email_1062():
    """Check the latest email to see what happened"""
    print("🔍 Debugging Email 1062")
    print("=" * 60)
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Get email 1062
        cursor.execute("""
            SELECT id, sender, subject, body, created_at, message_id, attachments
            FROM customer_emails 
            WHERE id = 1062
        """)
        
        email = cursor.fetchone()
        if not email:
            print("❌ Email 1062 not found")
            return False
        
        id, sender, subject, body, created_at, message_id, attachments = email
        
        print(f"📧 Email 1062 Details:")
        print(f"  ID: {id}")
        print(f"  Sender: {sender}")
        print(f"  Subject: {subject}")
        print(f"  Created: {created_at}")
        print(f"  Message ID: {message_id}")
        print(f"  Attachments: {attachments}")
        
        # Check if there are other emails with the same Message-ID
        cursor.execute("""
            SELECT id, sender, subject, created_at, attachments
            FROM customer_emails 
            WHERE message_id = %s
            ORDER BY created_at
        """, (message_id,))
        
        duplicates = cursor.fetchall()
        print(f"\n🔍 Emails with same Message-ID ({message_id}):")
        for dup in duplicates:
            eid, esender, esubject, ecreated, eattachments = dup
            print(f"  ID {eid}: {esubject}")
            print(f"    Sender: {esender}")
            print(f"    Created: {ecreated}")
            print(f"    Attachments: {eattachments}")
            print()
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False

def check_email_ingestor_code():
    """Check if the email_ingestor.py file has the updated code"""
    print(f"\n📄 Checking Email Ingestor Code:")
    print("-" * 60)
    
    try:
        with open('email_ingestor.py', 'r') as f:
            content = f.read()
        
        # Look for the old duplicate logic
        if "Skipping duplicate email with Message-ID" in content:
            print("❌ OLD duplicate logic still present")
        else:
            print("✅ OLD duplicate logic removed")
        
        # Look for the new duplicate logic
        if "Duplicate detected - update existing email with attachments" in content:
            print("✅ NEW duplicate logic found")
        else:
            print("❌ NEW duplicate logic missing")
        
        # Look for the specific line that should be updated
        if "ON CONFLICT (message_id) DO NOTHING" in content:
            print("❌ OLD SQL conflict handling still present")
        else:
            print("✅ OLD SQL conflict handling removed")
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")

def check_server_restart():
    """Check if the server needs to be restarted"""
    print(f"\n🔄 Server Restart Check:")
    print("-" * 60)
    
    print("The email_ingestor.py changes require the server to be restarted.")
    print("If you're running the email scheduler or Flask server, you need to:")
    print("1. Stop the current server (Ctrl+C)")
    print("2. Restart the server to load the updated code")
    print("3. Test with a new email")

def main():
    """Main function"""
    print("🚀 Duplicate Logic Debug")
    print("=" * 60)
    
    check_email_1062()
    check_email_ingestor_code()
    check_server_restart()
    
    print(f"\n💡 Next Steps:")
    print("1. Restart your Flask server or email scheduler")
    print("2. Send another test email")
    print("3. Check if the new duplicate logic is working")

if __name__ == "__main__":
    main() 