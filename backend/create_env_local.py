#!/usr/bin/env python3
"""
Create .env.local file with your correct database credentials
"""
import os

def create_env_local():
    """Create .env.local file with user input"""
    print("🔧 Creating .env.local file with your database credentials")
    print("=" * 60)
    
    # Check if .env.local already exists
    if os.path.exists('.env.local'):
        print("⚠️  .env.local already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            return False
    
    print("\n📊 Please enter your correct database credentials:")
    print("(These should be the same credentials that were working before)")
    
    # Get database credentials
    db_host = input("Database Host: ").strip()
    db_name = input("Database Name: ").strip()
    db_user = input("Database User: ").strip()
    db_password = input("Database Password: ").strip()
    db_port = input("Database Port (default: 5432): ").strip() or "5432"
    
    if not all([db_host, db_name, db_user, db_password]):
        print("❌ All database fields are required!")
        return False
    
    # Get other required variables
    print("\n🔑 Security Keys:")
    jwt_secret = input("JWT Secret Key: ").strip() or "local-jwt-secret-key"
    encryption_key = input("Encryption Key: ").strip() or "local-encryption-key"
    
    print("\n🤖 OpenAI (optional):")
    openai_key = input("OpenAI API Key (optional): ").strip()
    
    print("\n📧 Email (optional):")
    email_username = input("Email Username (optional): ").strip()
    email_password = input("Email Password (optional): ").strip()
    
    # Create .env.local content
    env_content = f"""# ========================================
# LOCAL DEVELOPMENT ENVIRONMENT VARIABLES
# Created with your working database credentials
# ========================================

# === FLASK ENVIRONMENT ===
FLASK_ENV=local
FLASK_DEBUG=true

# === DATABASE (Your Working Credentials) ===
DB_HOST={db_host}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_PORT={db_port}

# === SECURITY KEYS ===
JWT_SECRET_KEY={jwt_secret}
ENCRYPTION_KEY={encryption_key}

# === EMAIL SETTINGS ===
EMAIL_HOST=imap.gmail.com
EMAIL_USERNAME={email_username}
EMAIL_PASSWORD={email_password}
EMAIL_PORT=587

# SMTP Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME={email_username}
SMTP_PASSWORD={email_password}
FROM_EMAIL={email_username}

# === OPENAI SETTINGS ===
OPENAI_API_KEY={openai_key}

# === CORS SETTINGS ===
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000

# === EMAIL SCHEDULER SETTINGS ===
EMAIL_CHECK_INTERVAL=900
AUTO_SEND_ENABLED=true
CONFIDENCE_THRESHOLD=0.8

# === LOGGING SETTINGS ===
LOG_LEVEL=DEBUG
ENABLE_EMAIL_LOGGING=true

# === FILE UPLOAD SETTINGS ===
MAX_EMAIL_SIZE=10485760
ALLOWED_ATTACHMENT_TYPES=pdf,jpg,jpeg,png

# === LOCAL DEVELOPMENT OVERRIDES ===
FORCE_HTTPS=0
JWT_COOKIE_SECURE=false
JWT_COOKIE_SAMESITE=Lax
"""
    
    # Write .env.local file
    try:
        with open('.env.local', 'w') as f:
            f.write(env_content)
        
        print(f"\n✅ .env.local created successfully!")
        print(f"📁 File location: {os.path.abspath('.env.local')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating .env.local: {e}")
        return False

def test_connection():
    """Test the database connection"""
    print("\n🧪 Testing database connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv('.env.local')
        
        from config import get_db_conn
        conn = get_db_conn()
        
        if conn:
            print("✅ Database connection successful!")
            
            # Test a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"📊 PostgreSQL version: {version}")
            
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ Database connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Create .env.local with Correct Database Credentials")
    print("=" * 60)
    
    # Create .env.local
    if not create_env_local():
        return
    
    # Test connection
    if test_connection():
        print("\n🎉 Setup completed successfully!")
        print("\n💡 Now you can:")
        print("  1. Test attachments: python check_current_schema.py")
        print("  2. Start backend: python run_local.py")
        print("  3. Check if attachments show in CustomerEmails.js")
    else:
        print("\n⚠️  Setup completed but database connection failed.")
        print("💡 Please check your database credentials and try again.")

if __name__ == "__main__":
    main() 