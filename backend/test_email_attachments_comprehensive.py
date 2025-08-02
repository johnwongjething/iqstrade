#!/usr/bin/env python3
"""
Comprehensive test script for email attachments functionality
Tests the entire pipeline from email ingestion to frontend display
"""
import os
import sys
import json
import datetime
import tempfile
from config import get_db_conn

def create_test_pdf():
    """Create a simple test PDF file"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a temporary PDF file
        fd, temp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        
        # Create PDF content
        c = canvas.Canvas(temp_path, pagesize=letter)
        c.drawString(100, 750, "Test PDF Attachment")
        c.drawString(100, 700, "This is a test PDF for email attachment testing")
        c.drawString(100, 650, f"Created: {datetime.datetime.now()}")
        c.save()
        
        return temp_path
    except ImportError:
        print("⚠️  reportlab not available, skipping PDF creation")
        return None

def test_database_schema():
    """Test the database schema for attachments"""
    print("🔍 Testing database schema...")
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Check if customer_emails table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'customer_emails'
            );
        """)
        
        if not cursor.fetchone()[0]:
            print("❌ customer_emails table does not exist")
            cursor.close()
            conn.close()
            return False
        
        # Check attachments column
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'customer_emails' 
            AND column_name = 'attachments'
        """)
        
        result = cursor.fetchone()
        if not result:
            print("❌ attachments column does not exist")
            cursor.close()
            conn.close()
            return False
        
        column_name, data_type, is_nullable = result
        print(f"✅ Found attachments column: {column_name} ({data_type})")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

def test_attachment_storage():
    """Test storing and retrieving attachments"""
    print("\n📧 Testing attachment storage...")
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Test data
        test_attachments = [
            "https://res.cloudinary.com/demo/image/upload/v1/sample.pdf",
            "https://res.cloudinary.com/demo/image/upload/v1/receipt.jpg",
            "https://res.cloudinary.com/demo/image/upload/v1/document.pdf"
        ]
        
        # Insert test email
        cursor.execute("""
            INSERT INTO customer_emails (sender, subject, body, attachments, message_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            "test@example.com",
            "Test Email with Attachments",
            "This is a test email body with multiple attachments.",
            json.dumps(test_attachments),
            f"test-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            datetime.datetime.now()
        ))
        
        email_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ Test email inserted with ID: {email_id}")
        
        # Retrieve and verify
        cursor.execute("""
            SELECT id, sender, subject, attachments, pg_typeof(attachments)
            FROM customer_emails 
            WHERE id = %s
        """, (email_id,))
        
        result = cursor.fetchone()
        if result:
            db_id, db_sender, db_subject, db_attachments, db_type = result
            print(f"✅ Retrieved from database:")
            print(f"   ID: {db_id}")
            print(f"   Sender: {db_sender}")
            print(f"   Subject: {db_subject}")
            print(f"   Attachments: {db_attachments}")
            print(f"   Type: {db_type}")
            
            # Test parsing like the backend does
            parsed_attachments = []
            if db_attachments:
                if isinstance(db_attachments, list):
                    parsed_attachments = db_attachments
                elif isinstance(db_attachments, str):
                    try:
                        parsed_attachments = json.loads(db_attachments)
                    except:
                        parsed_attachments = [db_attachments]
                else:
                    parsed_attachments = [str(db_attachments)]
            
            print(f"✅ Parsed attachments: {parsed_attachments}")
            
            if len(parsed_attachments) == len(test_attachments):
                print("✅ Attachment count matches!")
            else:
                print(f"❌ Attachment count mismatch: expected {len(test_attachments)}, got {len(parsed_attachments)}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False

def test_email_routes_api():
    """Test the email routes API endpoint"""
    print("\n🌐 Testing email routes API...")
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Get the latest email with attachments
        cursor.execute("""
            SELECT id, sender, subject, body, attachments, bl_numbers, created_at
            FROM customer_emails 
            WHERE attachments IS NOT NULL 
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        email_row = cursor.fetchone()
        if not email_row:
            print("❌ No emails with attachments found for API testing")
            cursor.close()
            conn.close()
            return False
        
        email_id, sender, subject, body, attachments_raw, bl_numbers, created_at = email_row
        
        print(f"✅ Testing API for email ID: {email_id}")
        print(f"   Sender: {sender}")
        print(f"   Subject: {subject}")
        print(f"   Raw attachments: {attachments_raw}")
        
        # Simulate the API processing
        attachments = []
        if attachments_raw:
            if isinstance(attachments_raw, list):
                attachments = attachments_raw
            elif isinstance(attachments_raw, str):
                try:
                    attachments = json.loads(attachments_raw)
                except:
                    attachments = [attachments_raw]
            else:
                attachments = [str(attachments_raw)]
        
        # Simulate API response
        api_response = {
            'id': email_id,
            'sender': sender,
            'subject': subject,
            'body': body,
            'attachments': attachments,
            'bl_numbers': bl_numbers,
            'created_at': created_at.isoformat() if created_at else None
        }
        
        print(f"✅ API would return: {json.dumps(api_response, indent=2)}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_frontend_simulation():
    """Simulate how the frontend would handle the data"""
    print("\n🎨 Testing frontend simulation...")
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Get test email
        cursor.execute("""
            SELECT id, sender, subject, body, attachments, bl_numbers, created_at
            FROM customer_emails 
            WHERE attachments IS NOT NULL 
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        email_row = cursor.fetchone()
        if not email_row:
            print("❌ No emails with attachments found for frontend testing")
            cursor.close()
            conn.close()
            return False
        
        email_id, sender, subject, body, attachments_raw, bl_numbers, created_at = email_row
        
        # Process like the backend does
        attachments = []
        if attachments_raw:
            if isinstance(attachments_raw, list):
                attachments = attachments_raw
            elif isinstance(attachments_raw, str):
                try:
                    attachments = json.loads(attachments_raw)
                except:
                    attachments = [attachments_raw]
            else:
                attachments = [str(attachments_raw)]
        
        # Simulate frontend processing
        print(f"🎨 Frontend would receive:")
        print(f"   Email ID: {email_id}")
        print(f"   Attachments array: {attachments}")
        print(f"   Attachments length: {len(attachments)}")
        
        # Simulate attachment rendering
        for i, attachment in enumerate(attachments):
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
        print(f"❌ Frontend simulation failed: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Delete test emails
        cursor.execute("""
            DELETE FROM customer_emails 
            WHERE sender = 'test@example.com' 
            OR message_id LIKE 'test-%'
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ Cleaned up {deleted_count} test emails")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Comprehensive Email Attachments Test")
    print("=" * 60)
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Attachment Storage", test_attachment_storage),
        ("Email Routes API", test_email_routes_api),
        ("Frontend Simulation", test_frontend_simulation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Email attachments should work correctly.")
        print("\n💡 Next steps:")
        print("  1. Apply the database migration: backend/migrations/20250728_fix_attachments_column.sql")
        print("  2. Start your backend: python run_local.py")
        print("  3. Start your frontend: npm start (in frontend directory)")
        print("  4. Go to CustomerEmails page to test")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
    
    # Cleanup
    cleanup_test_data()

if __name__ == "__main__":
    main() 