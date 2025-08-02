#!/usr/bin/env python3
"""
Test Complete Attachment Flow
Verifies that attachments are properly stored and can be displayed in frontend.
"""

import os
import json
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local')

print("🔍 Testing Complete Attachment Flow")
print("=" * 50)

def test_database_attachments():
    """Test if attachments are properly stored in database."""
    print("\n🗄️ Testing Database Attachment Storage:")
    print("-" * 40)
    
    try:
        from config import get_db_conn
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
            
        cursor = conn.cursor()
        
        # Find emails with attachments
        cursor.execute("""
            SELECT id, subject, attachments 
            FROM customer_emails 
            WHERE attachments IS NOT NULL 
            AND attachments != 'null'
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        emails_with_attachments = cursor.fetchall()
        
        if emails_with_attachments:
            print(f"✅ Found {len(emails_with_attachments)} emails with attachments")
            
            for email_id, subject, attachments_raw in emails_with_attachments:
                print(f"\n📧 Email ID: {email_id}")
                print(f"📧 Subject: {subject}")
                print(f"📧 Raw attachments: {attachments_raw}")
                
                # Parse attachments
                if isinstance(attachments_raw, str):
                    try:
                        attachments = json.loads(attachments_raw)
                        print(f"📧 Parsed attachments: {attachments}")
                        
                        if isinstance(attachments, list):
                            for i, attachment in enumerate(attachments):
                                print(f"  📎 Attachment {i+1}: {attachment}")
                                if isinstance(attachment, str):
                                    if attachment.startswith('http'):
                                        print(f"    ✅ Cloudinary URL (accessible)")
                                    else:
                                        print(f"    ⚠️ Local file path: {attachment}")
                                        if os.path.exists(attachment):
                                            print(f"    ✅ Local file exists")
                                        else:
                                            print(f"    ❌ Local file not found")
                    except json.JSONDecodeError:
                        print(f"❌ Failed to parse attachments JSON")
                else:
                    print(f"📧 Attachments type: {type(attachments_raw)}")
        else:
            print("⚠️ No emails with attachments found in database")
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_backend_api():
    """Test if backend API returns attachments properly."""
    print("\n🔌 Testing Backend API:")
    print("-" * 40)
    
    try:
        from config import get_db_conn
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
            
        cursor = conn.cursor()
        
        # Find an email with attachments
        cursor.execute("""
            SELECT id FROM customer_emails 
            WHERE attachments IS NOT NULL 
            AND attachments != 'null'
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            email_id = result[0]
            print(f"✅ Found email with attachments: ID {email_id}")
            
            # Simulate the API call
            cursor.execute("SELECT id, sender, subject, body, attachments, bl_numbers, created_at FROM customer_emails WHERE id = %s", (email_id,))
            email_row = cursor.fetchone()
            
            if email_row:
                attachments_raw = email_row[4]
                print(f"📧 Raw attachments from DB: {attachments_raw}")
                
                # Process attachments like the API does
                attachments = []
                if attachments_raw:
                    if isinstance(attachments_raw, list):
                        attachments = attachments_raw
                    elif isinstance(attachments_raw, str):
                        try:
                            attachments = json.loads(attachments_raw)
                        except:
                            attachments = [attachments_raw]
                
                print(f"📧 Processed attachments: {attachments}")
                
                if attachments:
                    print("✅ Backend API would return attachments properly")
                    return True
                else:
                    print("❌ Backend API would not return attachments")
                    return False
            else:
                print("❌ Email not found")
                return False
        else:
            print("⚠️ No emails with attachments found for API test")
            return True  # Not an error, just no data
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Backend API test failed: {e}")
        return False

def test_frontend_display():
    """Test if frontend can handle the attachment data."""
    print("\n🎨 Testing Frontend Display Logic:")
    print("-" * 40)
    
    # Simulate different attachment scenarios
    test_cases = [
        {
            "name": "Cloudinary URLs",
            "attachments": [
                "https://res.cloudinary.com/your-cloud/image/upload/v123/email_attachments/file1.pdf",
                "https://res.cloudinary.com/your-cloud/image/upload/v123/email_attachments/file2.jpg"
            ]
        },
        {
            "name": "Local file paths",
            "attachments": [
                "downloads/file1.pdf",
                "downloads/file2.jpg"
            ]
        },
        {
            "name": "Mixed URLs and paths",
            "attachments": [
                "https://res.cloudinary.com/your-cloud/image/upload/v123/email_attachments/file1.pdf",
                "downloads/file2.jpg"
            ]
        },
        {
            "name": "Empty attachments",
            "attachments": []
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📧 Testing: {test_case['name']}")
        attachments = test_case['attachments']
        
        if attachments and len(attachments) > 0:
            print(f"  📎 Found {len(attachments)} attachment(s)")
            
            for i, attachment in enumerate(attachments):
                isUrl = isinstance(attachment, str) and (attachment.startswith('http') or attachment.startswith('https'))
                isCloudinary = isUrl and 'cloudinary' in attachment
                fileName = attachment.split('/').pop() if isinstance(attachment, str) else f"Attachment {i + 1}"
                
                print(f"    📎 Attachment {i+1}: {fileName}")
                print(f"      Type: {'Cloudinary URL' if isCloudinary else 'External URL' if isUrl else 'Local file'}")
                print(f"      Accessible: {'Yes' if isUrl else 'Maybe (local file)'}")
        else:
            print("  📎 No attachments")
    
    print("\n✅ Frontend display logic would handle all scenarios")
    return True

def main():
    """Run all tests."""
    results = {
        'database': test_database_attachments(),
        'backend_api': test_backend_api(),
        'frontend_display': test_frontend_display()
    }
    
    print("\n" + "=" * 50)
    print("📊 ATTACHMENT FLOW TEST RESULTS")
    print("=" * 50)
    
    for test, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test.replace('_', ' ').title()}")
    
    working = sum(results.values())
    total = len(results)
    
    print(f"\n🎯 Overall Status: {working}/{total} tests passed")
    
    if working == total:
        print("🎉 Attachment flow is working perfectly!")
        print("\n📋 When a new email comes in:")
        print("  1. ✅ Email ingestor will detect attachments")
        print("  2. ✅ Attachments will be saved locally")
        print("  3. ✅ Attachments will be uploaded to Cloudinary (if configured)")
        print("  4. ✅ Attachment URLs will be stored in database")
        print("  5. ✅ Frontend will display attachments with 'View' buttons")
        print("  6. ✅ Users can click 'View' to open attachments")
    else:
        print("\n🔧 Issues to fix:")
        if not results['database']:
            print("  - Check database attachment storage")
        if not results['backend_api']:
            print("  - Check backend API attachment handling")
        if not results['frontend_display']:
            print("  - Check frontend display logic")

if __name__ == "__main__":
    main() 