#!/usr/bin/env python3
"""
Debug environment variable loading
"""
import os
from dotenv import load_dotenv

def debug_env():
    """Debug environment variables"""
    print("🔍 Debugging environment variables...")
    
    # Check if .env.local exists
    env_file = os.path.join(os.path.dirname(__file__), '.env.local')
    print(f"📁 Looking for .env.local at: {env_file}")
    print(f"   Exists: {os.path.exists(env_file)}")
    
    if os.path.exists(env_file):
        print(f"   Size: {os.path.getsize(env_file)} bytes")
    
    # Load .env.local
    print("\n📋 Loading .env.local...")
    load_dotenv(env_file)
    
    # Check key database variables
    db_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_PORT']
    print("\n📊 Database variables:")
    for var in db_vars:
        value = os.getenv(var)
        if value:
            # Mask password
            if var == 'DB_PASSWORD':
                masked = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
                print(f"   {var}: {masked}")
            else:
                print(f"   {var}: {value}")
        else:
            print(f"   {var}: ❌ NOT SET")
    
    # Check if we have all required DB vars
    missing = [var for var in db_vars if not os.getenv(var)]
    if missing:
        print(f"\n❌ Missing database variables: {missing}")
    else:
        print(f"\n✅ All database variables are set")
        
        # Try to construct connection string
        db_host = os.getenv('DB_HOST')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_port = os.getenv('DB_PORT', '5432')
        
        connection_string = f"postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}"
        print(f"🔗 Connection string: {connection_string}")
    
    # Check other important variables
    other_vars = ['JWT_SECRET_KEY', 'ENCRYPTION_KEY', 'OPENAI_API_KEY']
    print(f"\n🔑 Other important variables:")
    for var in other_vars:
        value = os.getenv(var)
        if value:
            if var == 'OPENAI_API_KEY':
                masked = value[:10] + '***' if len(value) > 10 else '***'
                print(f"   {var}: {masked}")
            else:
                print(f"   {var}: ✅ SET")
        else:
            print(f"   {var}: ❌ NOT SET")

if __name__ == "__main__":
    debug_env() 