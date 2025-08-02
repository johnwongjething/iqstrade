#!/usr/bin/env python3
"""
Setup .env.local file for Email System
Helps you create the required environment variables file
"""

import os

def create_env_local_template():
    """Create a template .env.local file"""
    
    template = """# Email Configuration
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_HOST=smtp.gmail.com

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Database Configuration
DB_NAME=your-database-name
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_HOST=your-database-host
DB_PORT=5432

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
CLOUDINARY_BASE_URL=https://res.cloudinary.com/your-cloud-name

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-this-in-production

# Email Scheduler
ENABLE_EMAIL_SCHEDULER=true
"""
    
    # Check if .env.local already exists
    env_file = os.path.join(os.path.dirname(__file__), '.env.local')
    
    if os.path.exists(env_file):
        print("⚠️ .env.local file already exists!")
        print("Please edit the existing file with your actual values.")
        return False
    
    # Create the file
    try:
        with open(env_file, 'w') as f:
            f.write(template)
        
        print("✅ Created .env.local template file")
        print(f"📁 Location: {env_file}")
        print("\n📋 Next Steps:")
        print("1. Edit .env.local with your actual values")
        print("2. Replace 'your-email@gmail.com' with your Gmail address")
        print("3. Replace 'your-app-password' with your Gmail app password")
        print("4. Replace 'your-openai-api-key' with your OpenAI API key")
        print("5. Replace database values with your actual database credentials")
        print("6. Replace Cloudinary values with your actual Cloudinary credentials")
        print("\n🔒 Security Note: Never commit .env.local to version control!")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env.local: {e}")
        return False

def print_setup_instructions():
    """Print detailed setup instructions"""
    print("\n" + "="*60)
    print("📧 EMAIL SYSTEM SETUP INSTRUCTIONS")
    print("="*60)
    
    print("\n🔑 Required Environment Variables:")
    print("1. EMAIL_USERNAME - Your Gmail address")
    print("2. EMAIL_PASSWORD - Your Gmail app password (not regular password)")
    print("3. EMAIL_HOST - SMTP server (usually smtp.gmail.com)")
    print("4. OPENAI_API_KEY - Your OpenAI API key")
    print("5. DB_NAME, DB_USER, DB_PASSWORD, DB_HOST - Database credentials")
    print("6. CLOUDINARY_* - Cloudinary credentials for file storage")
    
    print("\n📧 Gmail Setup:")
    print("1. Enable 2-factor authentication on your Gmail account")
    print("2. Generate an App Password: Google Account > Security > App Passwords")
    print("3. Use the generated password as EMAIL_PASSWORD")
    
    print("\n🤖 OpenAI Setup:")
    print("1. Go to https://platform.openai.com/api-keys")
    print("2. Create a new API key")
    print("3. Use it as OPENAI_API_KEY")
    
    print("\n☁️ Cloudinary Setup:")
    print("1. Sign up at https://cloudinary.com")
    print("2. Get your cloud name, API key, and API secret")
    print("3. Use them in the CLOUDINARY_* variables")

def main():
    """Main function"""
    print("🚀 Email System Environment Setup")
    print("="*50)
    
    # Create template
    success = create_env_local_template()
    
    if success:
        print_setup_instructions()
    else:
        print("\n📋 Manual Setup:")
        print("1. Create a file named '.env.local' in the backend directory")
        print("2. Add the environment variables listed above")
        print("3. Replace placeholder values with your actual credentials")

if __name__ == "__main__":
    main() 