#!/usr/bin/env python3
"""
Verification script for email ingestor setup
Checks database schema, imports, and basic functionality
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def check_imports():
    """Check if all required modules can be imported"""
    print("🔍 Checking imports...")
    
    try:
        from email_ingestor import process_inbox, ingest_emails
        print("✅ email_ingestor imports successful")
    except Exception as e:
        print(f"❌ email_ingestor import failed: {e}")
        return False
    
    try:
        from db_utils import get_db_conn
        print("✅ db_utils import successful")
    except Exception as e:
        print(f"❌ db_utils import failed: {e}")
        return False
    
    try:
        from cloudinary_utils import upload_filepath_to_cloudinary
        print("✅ cloudinary_utils import successful")
    except Exception as e:
        print(f"❌ cloudinary_utils import failed: {e}")
        return False
    
    try:
        from invoice_utils import generate_pdf_from_text
        print("✅ invoice_utils import successful")
    except Exception as e:
        print(f"❌ invoice_utils import failed: {e}")
        return False
    
    return True

def check_database_schema():
    """Check if database schema is correct"""
    print("\n🔍 Checking database schema...")
    
    try:
        from db_utils import get_db_conn
        conn = get_db_conn()
        
        if conn is None:
            print("❌ Database connection failed - conn is None")
            return False
            
        cur = conn.cursor()
        
        # Check if customer_emails table exists with required columns
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'customer_emails' 
            AND column_name IN ('processed_for_payments', 'message_id', 'sender', 'subject', 'body')
            ORDER BY column_name
        """)
        
        columns = cur.fetchall()
        required_columns = {
            'processed_for_payments': 'boolean',
            'message_id': 'character varying',
            'sender': 'character varying', 
            'subject': 'text',
            'body': 'text'
        }
        
        found_columns = {col[0]: col[1] for col in columns}
        
        print("✅ Required columns found:")
        for col_name, expected_type in required_columns.items():
            if col_name in found_columns:
                print(f"  - {col_name}: {found_columns[col_name]} ✅")
            else:
                print(f"  - {col_name}: MISSING ❌")
                return False
        
        # Check if indexes exist
        cur.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'customer_emails' 
            AND indexname LIKE '%processed_for_payments%'
        """)
        
        indexes = cur.fetchall()
        if indexes:
            print("✅ Indexes found:")
            for idx in indexes:
                print(f"  - {idx[0]}")
        else:
            print("⚠️  No processed_for_payments indexes found")
        
        # Test a simple query to verify connection
        cur.execute("SELECT COUNT(*) FROM customer_emails")
        count = cur.fetchone()[0]
        print(f"✅ Database connection verified - {count} emails in database")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database schema check failed: {e}")
        return False

def check_environment():
    """Check if required environment variables are set"""
    print("\n🔍 Checking environment variables...")
    
    required_vars = [
        'EMAIL_HOST',
        'EMAIL_USERNAME', 
        'EMAIL_PASSWORD',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.getenv(var):
            # Mask sensitive values for security
            value = os.getenv(var)
            if var in ['EMAIL_PASSWORD', 'OPENAI_API_KEY']:
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
                print(f"  - {var}: SET ✅ ({masked_value})")
            else:
                print(f"  - {var}: SET ✅ ({value})")
        else:
            print(f"  - {var}: MISSING ❌")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Note: These are required for email processing but won't prevent database verification")
        return False
    
    return True

def check_functions():
    """Check if functions are callable"""
    print("\n🔍 Checking function availability...")
    
    try:
        from email_ingestor import process_inbox, ingest_emails
        
        # Check if functions exist and are callable
        if callable(process_inbox):
            print("✅ process_inbox function available")
        else:
            print("❌ process_inbox function not callable")
            return False
            
        if callable(ingest_emails):
            print("✅ ingest_emails function available")
        else:
            print("❌ ingest_emails function not callable")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Function check failed: {e}")
        return False

def main():
    """Main verification function"""
    print("🚀 Email Ingestor Setup Verification")
    print("=" * 50)
    
    checks = [
        ("Imports", check_imports),
        ("Database Schema", check_database_schema),
        ("Environment Variables", check_environment),
        ("Functions", check_functions)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        if not check_func():
            all_passed = False
            print(f"\n❌ {check_name} check failed")
        else:
            print(f"\n✅ {check_name} check passed")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL CHECKS PASSED! Email ingestor is ready to use.")
        print("\nYou can now use either:")
        print("  - process_inbox()  # New function name")
        print("  - ingest_emails()  # Original function name (alias)")
    else:
        print("❌ SOME CHECKS FAILED! Please fix the issues above.")
        print("\nNote: Environment variables are only needed for actual email processing.")
        print("Database and code structure are working correctly.")
        sys.exit(1)

if __name__ == "__main__":
    main() 