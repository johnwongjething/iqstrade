#!/usr/bin/env python3
"""
Simple database connection test to diagnose hanging issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_db_connection():
    """Test basic database connection"""
    try:
        print("Testing database connection...")
        
        # Import database utilities
        from db_utils import get_db_conn
        
        print("Attempting to connect to database...")
        conn = get_db_conn()
        
        if conn:
            print("✅ Database connection successful!")
            
            # Test a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Database version: {version[0]}")
            
            # Test the email processing locks table
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'email_processing_locks');")
            table_exists = cursor.fetchone()[0]
            print(f"✅ Email processing locks table exists: {table_exists}")
            
            cursor.close()
            conn.close()
            print("✅ Database connection test completed successfully!")
            return True
        else:
            print("❌ Database connection failed - no connection returned")
            return False
            
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_db_connection()
    sys.exit(0 if success else 1)