#!/usr/bin/env python3
"""
Test API response for email details
"""
import os
import json
from config import get_db_conn

def test_api_response():
    """Test what the API would return for an email with attachments"""
    print("🌐 Testing API response for email details...")
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return
        
        cursor = conn.cursor()
        
        # Get the latest email with attachments
        cursor.execute("""
            SELECT id, sender, subject, body, attachments, bl_numbers, created_at
            FROM customer_emails 
            WHERE attachments IS NOT NULL AND attachments != '[]' AND attachments != 'null'
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        email_row = cursor.fetchone()
        if not email_row:
            print("❌ No emails with attachments found")
            cursor.close()
            conn.close()
            return
        
        email_id, sender, subject, body, attachments_raw, bl_numbers, created_at = email_row
        
        print(f"✅ Testing API for email ID: {email_id}")
        print(f"   Sender: {sender}")
        print(f"   Subject: {subject}")
        print(f"   Raw attachments from DB: {attachments_raw}")
        print(f"   Attachments type: {type(attachments_raw)}")
        
        # Simulate the API processing (like email_routes.py does)
        attachments = []
        if attachments_raw:
            if isinstance(attachments_raw, list):
                attachments = attachments_raw
            elif isinstance(attachments_raw, str):
                try:
                    parsed = json.loads(attachments_raw)
                    if isinstance(parsed, list):
                        attachments = parsed
                    else:
                        attachments = [parsed]
                except json.JSONDecodeError:
                    attachments = [attachments_raw]
            else:
                attachments = [str(attachments_raw)]
        
        print(f"   Processed attachments: {attachments}")
        print(f"   Processed type: {type(attachments)}")
        print(f"   Processed length: {len(attachments)}")
        
        # Get replies for this email
        cursor.execute("""
            SELECT id, sender, body, created_at 
            FROM customer_email_replies 
            WHERE customer_email_id = %s 
            ORDER BY created_at ASC
        """, (email_id,))
        
        replies = [
            {
                'id': r[0],
                'sender': r[1],
                'body': r[2],
                'created_at': r[3].isoformat() if r[3] else None
            } for r in cursor.fetchall()
        ]
        
        # Simulate API response
        api_response = {
            'id': email_id,
            'sender': sender,
            'subject': subject,
            'body': body,
            'attachments': attachments,
            'bl_numbers': bl_numbers,
            'created_at': created_at.isoformat() if created_at else None,
            'replies': replies
        }
        
        print(f"\n📤 API would return:")
        print(json.dumps(api_response, indent=2))
        
        # Test what the frontend would receive
        print(f"\n🎨 Frontend would receive:")
        print(f"   attachments: {api_response['attachments']}")
        print(f"   attachments type: {type(api_response['attachments'])}")
        print(f"   attachments length: {len(api_response['attachments'])}")
        
        if api_response['attachments']:
            for i, attachment in enumerate(api_response['attachments']):
                isUrl = isinstance(attachment, str) and (attachment.startswith('http') or attachment.startswith('https'))
                isCloudinary = isUrl and 'cloudinary' in attachment
                fileName = attachment.split('/')[-1] if isinstance(attachment, str) else f"Attachment {i + 1}"
                
                print(f"   📎 Attachment {i + 1}:")
                print(f"      File: {fileName}")
                print(f"      URL: {isUrl}")
                print(f"      Cloudinary: {isCloudinary}")
                print(f"      Raw: {attachment}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    test_api_response() 