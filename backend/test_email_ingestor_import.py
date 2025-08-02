#!/usr/bin/env python3
"""
Test email_ingestor module import to diagnose hanging issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_email_ingestor_import():
    """Test importing email_ingestor module"""
    try:
        print("Testing email_ingestor import...")
        
        # Test basic imports first
        print("1. Testing basic imports...")
        import logging
        import email
        import json
        import tempfile
        import os
        print("✅ Basic imports successful")
        
        # Test database connection
        print("2. Testing database connection...")
        from db_utils import get_db_conn
        conn = get_db_conn()
        print("✅ Database connection successful")
        
        # Test email_ingestor import
        print("3. Testing email_ingestor import...")
        import email_ingestor
        print("✅ email_ingestor import successful")
        
        # Test specific functions
        print("4. Testing email_ingestor functions...")
        print(f"✅ acquire_db_processing_lock function exists: {hasattr(email_ingestor, 'acquire_db_processing_lock')}")
        print(f"✅ release_db_processing_lock function exists: {hasattr(email_ingestor, 'release_db_processing_lock')}")
        print(f"✅ get_db_processing_status function exists: {hasattr(email_ingestor, 'get_db_processing_status')}")
        print(f"✅ process_inbox function exists: {hasattr(email_ingestor, 'process_inbox')}")
        
        # Test database lock functions
        print("5. Testing database lock functions...")
        status = email_ingestor.get_db_processing_status()
        print(f"✅ get_db_processing_status result: {status}")
        
        conn.close()
        print("✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_email_ingestor_import()
    sys.exit(0 if success else 1) 