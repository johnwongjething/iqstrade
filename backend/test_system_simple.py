#!/usr/bin/env python3
"""
Simple system test to verify components are working
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_system_components():
    """Test basic system components"""
    try:
        print("🧪 Testing system components...")
        
        # Test 1: Database connection
        print("1. Testing database connection...")
        from db_utils import get_db_conn
        conn = get_db_conn()
        print("   ✅ Database connection successful")
        
        # Test 2: Minimal email ingestor
        print("2. Testing minimal email ingestor...")
        from email_ingestor_minimal import get_db_processing_status, process_inbox
        print("   ✅ Minimal email ingestor import successful")
        
        # Test 3: Database lock functions
        print("3. Testing database lock functions...")
        status = get_db_processing_status()
        print(f"   ✅ Processing status: {status}")
        
        # Test 4: Simple process_inbox call
        print("4. Testing process_inbox...")
        result = process_inbox(user_id='test_user')
        print(f"   ✅ Process inbox result: {result}")
        
        # Test 5: Check database tables
        print("5. Checking database tables...")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        email_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM email_processing_locks")
        lock_count = cursor.fetchone()[0]
        print(f"   ✅ customer_emails: {email_count} records")
        print(f"   ✅ email_processing_locks: {lock_count} records")
        
        cursor.close()
        conn.close()
        
        print("✅ All system components working!")
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_system_components()
    sys.exit(0 if success else 1) 