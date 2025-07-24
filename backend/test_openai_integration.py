#!/usr/bin/env python3
"""
Test script to verify OpenAI integration is working.
This will test the key components without requiring actual API calls.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test if required environment variables are set."""
    print("=== Testing Environment Variables ===")
    
    required_vars = [
        'OPENAI_API_KEY',
        'EMAIL_HOST',
        'EMAIL_USERNAME', 
        'EMAIL_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} (set)")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file")
        return False
    else:
        print("\n✅ All required environment variables are set")
        return True

def test_imports():
    """Test if all required modules can be imported."""
    print("\n=== Testing Module Imports ===")
    
    modules_to_test = [
        'openai',
        'ocr_processor',
        'email_ingestor',
        'extract_fields'
    ]
    
    failed_imports = []
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}: imported successfully")
        except ImportError as e:
            print(f"❌ {module}: import failed - {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n⚠️  Failed imports: {', '.join(failed_imports)}")
        return False
    else:
        print("\n✅ All modules imported successfully")
        return True

def test_database_connection():
    """Test database connection and required tables."""
    print("\n=== Testing Database Connection ===")
    
    try:
        from config import get_db_conn
        conn = get_db_conn()
        if conn:
            print("✅ Database connection successful")
            
            # Test if required tables exist
            cur = conn.cursor()
            
            tables_to_check = ['customer_emails', 'customer_email_replies']
            missing_tables = []
            
            for table in tables_to_check:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, (table,))
                exists = cur.fetchone()[0]
                if exists:
                    print(f"✅ Table {table}: exists")
                else:
                    print(f"❌ Table {table}: missing")
                    missing_tables.append(table)
            
            cur.close()
            conn.close()
            
            if missing_tables:
                print(f"\n⚠️  Missing tables: {', '.join(missing_tables)}")
                print("Please run the migration: 20250716_create_customer_email_tables.sql")
                return False
            else:
                print("\n✅ All required tables exist")
                return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_openai_client():
    """Test OpenAI client configuration."""
    print("\n=== Testing OpenAI Client ===")
    
    try:
        import openai
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not set")
            return False
        
        openai.api_key = api_key
        print("✅ OpenAI client configured")
        
        # Test a simple API call (optional - comment out if you want to avoid API usage)
        # try:
        #     response = openai.ChatCompletion.create(
        #         model="gpt-3.5-turbo",
        #         messages=[{"role": "user", "content": "Hello"}],
        #         max_tokens=5
        #     )
        #     print("✅ OpenAI API call successful")
        # except Exception as e:
        #     print(f"⚠️  OpenAI API call failed: {e}")
        #     print("This might be due to API key issues or rate limits")
        
        return True
    except Exception as e:
        print(f"❌ OpenAI client test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing OpenAI Integration for IQSTrade")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_imports,
        test_database_connection,
        test_openai_client
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OpenAI integration should be working.")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nNext steps:")
        print("1. Set missing environment variables in .env file")
        print("2. Run database migrations if tables are missing")
        print("3. Install missing Python packages if imports fail")
        print("4. Check OpenAI API key if API calls fail")

if __name__ == "__main__":
    main() 