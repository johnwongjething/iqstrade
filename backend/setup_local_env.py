#!/usr/bin/env python3
"""
Local Environment Setup Helper
Helps you copy environment variables from production to local development
"""

import os
import shutil
from pathlib import Path

def create_local_env_file():
    """Create .env.local file from template"""
    
    template_path = Path(__file__).parent / 'env_local_production_template.txt'
    local_env_path = Path(__file__).parent / '.env.local'
    
    if local_env_path.exists():
        print("⚠️  .env.local already exists!")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("❌ Setup cancelled")
            return False
    
    try:
        shutil.copy(template_path, local_env_path)
        print("✅ Created .env.local from template")
        return True
    except Exception as e:
        print(f"❌ Error creating .env.local: {e}")
        return False

def show_setup_instructions():
    """Show step-by-step setup instructions"""
    
    print("\n" + "=" * 60)
    print("📋 SETUP INSTRUCTIONS")
    print("=" * 60)
    
    print("\n1️⃣  Copy Environment Variables from Render:")
    print("   • Go to your Render dashboard")
    print("   • Navigate to Environment section")
    print("   • Copy these values to .env.local:")
    
    variables_to_copy = [
        "DATABASE_URL",
        "DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_PORT",
        "SECRET_KEY", "JWT_SECRET_KEY", "ENCRYPTION_KEY",
        "EMAIL_HOST", "EMAIL_USERNAME", "EMAIL_PASSWORD", "EMAIL_PORT",
        "SMTP_SERVER", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "FROM_EMAIL",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET",
        "GEETEST_ID", "GEETEST_KEY",
        "JWT_ACCESS_TOKEN_EXPIRES"
    ]
    
    for var in variables_to_copy:
        print(f"   • {var}")
    
    print("\n2️⃣  Get OpenAI API Key:")
    print("   • Go to https://platform.openai.com/api-keys")
    print("   • Create a new API key")
    print("   • Add it to .env.local as OPENAI_API_KEY")
    
    print("\n3️⃣  Test Your Setup:")
    print("   • Run: python test_local_setup.py")
    print("   • Fix any issues reported")
    
    print("\n4️⃣  Start Development:")
    print("   • Backend: python run_local.py")
    print("   • Frontend: cd frontend && npm start")
    
    print("\n" + "=" * 60)

def check_current_env():
    """Check if .env.local exists and show status"""
    
    local_env_path = Path(__file__).parent / '.env.local'
    
    if not local_env_path.exists():
        print("❌ .env.local file not found")
        return False
    
    print("✅ .env.local file exists")
    
    # Load and check key variables
    from dotenv import load_dotenv
    load_dotenv(local_env_path)
    
    key_vars = [
        'DATABASE_URL', 'SECRET_KEY', 'JWT_SECRET_KEY',
        'EMAIL_USERNAME', 'OPENAI_API_KEY'
    ]
    
    print("\n📊 Environment Variable Status:")
    for var in key_vars:
        value = os.getenv(var)
        if value and not value.startswith('your_') and not value.startswith('sk-your'):
            print(f"  ✅ {var}: Set")
        else:
            print(f"  ❌ {var}: Not set or using default")
    
    return True

def main():
    """Main setup function"""
    
    print("🚀 LOCAL ENVIRONMENT SETUP")
    print("=" * 60)
    
    # Check current status
    env_exists = check_current_env()
    
    if not env_exists:
        print("\n📝 Creating .env.local file...")
        if create_local_env_file():
            show_setup_instructions()
        else:
            print("❌ Failed to create .env.local")
            return
    else:
        print("\n📝 .env.local already exists")
        response = input("Do you want to see setup instructions? (y/N): ")
        if response.lower() == 'y':
            show_setup_instructions()
    
    print("\n🎯 Next Steps:")
    print("1. Edit .env.local with your actual values from Render")
    print("2. Run: python test_local_setup.py")
    print("3. Start development: python run_local.py")

if __name__ == '__main__':
    main() 