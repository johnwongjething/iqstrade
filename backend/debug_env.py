#!/usr/bin/env python3
"""
Debug Environment Variables and Database Connection
"""

import os
from dotenv import load_dotenv

print("🔍 Debug Environment Variables")
print("=" * 50)

# Load environment
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
print(f"Looking for .env.local at: {env_file}")
print(f"File exists: {os.path.exists(env_file)}")

if os.path.exists(env_file):
    load_dotenv(env_file)
    print("✅ .env.local loaded")
else:
    print("❌ .env.local not found")

print("\n📋 Environment Variables:")
print("-" * 30)

# Database variables
db_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
for var in db_vars:
    value = os.getenv(var)
    if value:
        print(f"✅ {var}: {value[:10]}..." if len(value) > 10 else f"✅ {var}: {value}")
    else:
        print(f"❌ {var}: NOT SET")

# Email variables
email_vars = ['EMAIL_HOST', 'EMAIL_USERNAME', 'EMAIL_PASSWORD']
for var in email_vars:
    value = os.getenv(var)
    if value:
        print(f"✅ {var}: {value[:10]}..." if len(value) > 10 else f"✅ {var}: {value}")
    else:
        print(f"❌ {var}: NOT SET")

# OpenAI variable
openai_key = os.getenv('OPENAI_API_KEY')
if openai_key:
    print(f"✅ OPENAI_API_KEY: {openai_key[:20]}...")
else:
    print("❌ OPENAI_API_KEY: NOT SET")

print("\n🗄️ Testing Database Connection:")
print("-" * 30)

try:
    from config import get_db_conn
    print("✅ Config imported")
    
    conn = get_db_conn()
    if conn:
        print("✅ Database connection successful")
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ Database version: {version[:50]}...")
        cursor.close()
        conn.close()
    else:
        print("❌ Database connection failed")
        
except Exception as e:
    print(f"❌ Database error: {e}")

print("\n📧 Testing Email Configuration:")
print("-" * 30)

try:
    from email_ingestor import connect_imap
    print("✅ Email ingestor imported")
    
    # Just test the connection function exists
    print("✅ IMAP connection function available")
    
except Exception as e:
    print(f"❌ Email error: {e}")

print("\n�� Debug completed!") 