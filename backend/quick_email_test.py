#!/usr/bin/env python3
"""
Quick Email System Test
"""

print("🚀 Quick Email System Test")
print("=" * 40)

try:
    print("1. Testing imports...")
    from email_ingestor import process_inbox
    print("   ✅ Email ingestor imported successfully")
    
    print("2. Testing database connection...")
    from config import get_db_conn
    conn = get_db_conn()
    if conn:
        print("   ✅ Database connected")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        count = cursor.fetchone()[0]
        print(f"   📧 Found {count} emails in database")
        cursor.close()
        conn.close()
    else:
        print("   ❌ Database connection failed")
    
    print("3. Testing email processing...")
    print("   🔄 Processing inbox (this may take a moment)...")
    result = process_inbox()
    if result is not None:
        print(f"   ✅ Email processing completed - processed {len(result)} emails")
        if result:
            print(f"   📧 New emails found: {len(result)}")
        else:
            print("   📧 No new emails found")
    else:
        print("   ❌ Email processing failed")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n🎯 Test completed!") 