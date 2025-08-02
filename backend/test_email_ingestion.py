#!/usr/bin/env python3
"""
Test Email Ingestion Process
"""
import os
import sys
import tempfile
from config import get_db_conn
from cloudinary_utils import upload_filepath_to_cloudinary

def test_cloudinary_upload():
    """Test if Cloudinary upload is working"""
    print("☁️ Testing Cloudinary Upload")
    print("-" * 60)
    
    try:
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test file for Cloudinary upload")
            test_file_path = f.name
        
        print(f"📄 Created test file: {test_file_path}")
        
        # Try to upload to Cloudinary
        cloudinary_url = upload_filepath_to_cloudinary(test_file_path, folder="test_uploads")
        print(f"✅ Upload successful: {cloudinary_url}")
        
        # Clean up
        os.unlink(test_file_path)
        return True
        
    except Exception as e:
        print(f"❌ Cloudinary upload failed: {e}")
        return False

def test_email_ingestor_import():
    """Test if email_ingestor can be imported and has key functions"""
    print("\n📧 Testing Email Ingestor Import")
    print("-" * 60)
    
    try:
        import email_ingestor
        print("✅ email_ingestor imported successfully")
        
        # Check for key functions
        required_functions = ['process_inbox', 'connect_imap', 'ingest_emails']
        for func_name in required_functions:
            if hasattr(email_ingestor, func_name):
                print(f"✅ {func_name} function found")
            else:
                print(f"❌ {func_name} function missing")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import email_ingestor: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing email_ingestor: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("\n🗄️ Testing Database Connection")
    print("-" * 60)
    
    try:
        conn = get_db_conn()
        if conn:
            print("✅ Database connection successful")
            conn.close()
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

def check_email_scheduler_status():
    """Check if email scheduler is running"""
    print("\n⏰ Checking Email Scheduler Status")
    print("-" * 60)
    
    try:
        # Check if email_scheduler.py exists
        if os.path.exists('email_scheduler.py'):
            print("✅ email_scheduler.py found")
            
            # Try to import
            try:
                import email_scheduler
                print("✅ email_scheduler imported successfully")
                
                # Check if it has the main function
                if hasattr(email_scheduler, 'main'):
                    print("✅ main function found")
                else:
                    print("❌ main function missing")
                    
            except ImportError as e:
                print(f"❌ Cannot import email_scheduler: {e}")
        else:
            print("❌ email_scheduler.py not found")
            
    except Exception as e:
        print(f"❌ Error checking scheduler: {e}")

def suggest_next_steps():
    """Suggest next steps based on test results"""
    print("\n💡 Next Steps:")
    print("-" * 60)
    
    print("1. 🔧 If Cloudinary upload failed:")
    print("   - Check your Cloudinary credentials")
    print("   - Verify your Cloudinary account is active")
    print("   - Test with a simple file upload")
    
    print("\n2. 📧 If email_ingestor import failed:")
    print("   - Check if all dependencies are installed")
    print("   - Verify email_ingestor.py is not corrupted")
    print("   - Check for syntax errors")
    
    print("\n3. 🗄️ If database connection failed:")
    print("   - Verify your database is running")
    print("   - Check your .env.local credentials")
    print("   - Test connection manually")
    
    print("\n4. ⏰ To start email ingestion:")
    print("   - Run: python email_scheduler.py")
    print("   - Or: python start_email_service.py")
    print("   - Check logs for any errors")

def main():
    """Main function"""
    print("🚀 Email Ingestion System Test")
    print("=" * 60)
    
    # Run tests
    cloudinary_ok = test_cloudinary_upload()
    ingestor_ok = test_email_ingestor_import()
    db_ok = test_database_connection()
    check_email_scheduler_status()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"  Cloudinary Upload: {'✅ OK' if cloudinary_ok else '❌ FAILED'}")
    print(f"  Email Ingestor: {'✅ OK' if ingestor_ok else '❌ FAILED'}")
    print(f"  Database: {'✅ OK' if db_ok else '❌ FAILED'}")
    
    if cloudinary_ok and ingestor_ok and db_ok:
        print("\n✅ All systems are working!")
        print("The email ingestion should be able to process attachments.")
        print("Try starting the email scheduler to process new emails.")
    else:
        print("\n❌ Some systems are not working properly.")
        print("Please fix the issues above before starting email ingestion.")
    
    suggest_next_steps()

if __name__ == "__main__":
    main() 