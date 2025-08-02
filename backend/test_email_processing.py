#!/usr/bin/env python3
"""
Test email processing functionality directly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_email_processing():
    """Test email processing functionality"""
    try:
        print("🧪 Testing email processing functionality...")
        
        # Import the minimal email ingestor
        from email_ingestor_minimal import process_inbox, get_db_processing_status
        
        # Test 1: Check initial status
        print("1. Checking initial processing status...")
        status = get_db_processing_status()
        print(f"   📊 Status: {status}")
        
        # Test 2: Try to process emails (should work with minimal version)
        print("2. Testing email processing...")
        result = process_inbox(user_id='test_user')
        print(f"   📧 Result: {result}")
        
        # Test 3: Check status after processing
        print("3. Checking status after processing...")
        status_after = get_db_processing_status()
        print(f"   📊 Status after: {status_after}")
        
        # Test 4: Try manual email ingestion endpoint simulation
        print("4. Testing manual email ingestion simulation...")
        from routes.admin_routes import admin_ingest_emails
        
        # Create a mock user
        class MockUser:
            def get(self, key, default=None):
                return 'test_user' if key == 'username' else default
        
        mock_user = MockUser()
        
        # Test the endpoint function
        result = admin_ingest_emails()
        print(f"   🔄 Manual ingestion result: {result}")
        
        print("✅ Email processing test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Email processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_email_processing()
    sys.exit(0 if success else 1) 