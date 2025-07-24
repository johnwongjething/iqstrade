#!/usr/bin/env python3
"""
Test Local Development Setup
Verifies that all components are working correctly for local development
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load local environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

def test_environment_variables():
    """Test that required environment variables are set"""
    print("🔍 Testing Environment Variables...")
    
    required_vars = [
        'LOCAL_DATABASE_URL',
        'LOCAL_SECRET_KEY',
        'LOCAL_JWT_SECRET_KEY',
        'LOCAL_OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your-') or value.startswith('sk-your'):
            missing_vars.append(var)
        else:
            print(f"  ✅ {var}: Set")
    
    if missing_vars:
        print(f"  ❌ Missing or default values for: {', '.join(missing_vars)}")
        return False
    
    print("  ✅ All environment variables are properly configured")
    return True

def test_database_connection():
    """Test database connection"""
    print("\n🗄️  Testing Database Connection...")
    
    try:
        from config_local import get_local_db_conn
        conn = get_local_db_conn()
        
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            cur.close()
            conn.close()
            
            print(f"  ✅ Database connected: {version.split(',')[0]}")
            return True
        else:
            print("  ❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n🤖 Testing OpenAI API...")
    
    try:
        import openai
        api_key = os.getenv('LOCAL_OPENAI_API_KEY')
        
        if not api_key or api_key.startswith('sk-your'):
            print("  ⚠️  OpenAI API key not set (skipping test)")
            return True
        
        openai.api_key = api_key
        
        # Test with a simple request
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        print("  ✅ OpenAI API connection successful")
        return True
        
    except Exception as e:
        print(f"  ❌ OpenAI API error: {e}")
        return False

def test_flask_app():
    """Test Flask app configuration"""
    print("\n🌐 Testing Flask App Configuration...")
    
    try:
        from config_local import LocalConfig, get_config
        from flask import Flask
        
        # Create test app
        test_app = Flask(__name__)
        config = get_config()
        config.init_app(test_app)
        
        print(f"  ✅ Flask app configured")
        print(f"  ✅ Debug mode: {test_app.config.get('DEBUG', False)}")
        print(f"  ✅ CORS origins: {config.CORS_ORIGINS}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Flask configuration error: {e}")
        return False

def test_dependencies():
    """Test that all required dependencies are installed"""
    print("\n📦 Testing Dependencies...")
    
    required_packages = [
        'flask',
        'psycopg2',
        'openai',
        'schedule',
        'flask_cors',
        'flask_jwt_extended',
        'python_dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"\n  ⚠️  Missing packages: {', '.join(missing_packages)}")
        print("  Run: pip install -r requirements.txt")
        return False
    
    return True

def test_local_server():
    """Test if local server is running"""
    print("\n🚀 Testing Local Server...")
    
    try:
        response = requests.get('http://localhost:5000/test', timeout=5)
        if response.status_code == 200:
            print("  ✅ Local server is running")
            return True
        else:
            print(f"  ⚠️  Local server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ⚠️  Local server is not running (this is normal if you haven't started it)")
        print("  Start with: python run_local.py")
        return True
    except Exception as e:
        print(f"  ❌ Server test error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 LOCAL DEVELOPMENT SETUP TEST")
    print("=" * 60)
    
    tests = [
        test_environment_variables,
        test_dependencies,
        test_database_connection,
        test_openai_connection,
        test_flask_app,
        test_local_server
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your local setup is ready.")
        print("\n📋 Next steps:")
        print("  1. Start the backend: python run_local.py")
        print("  2. Start the frontend: cd frontend && npm start")
        print("  3. Open http://localhost:3000 in your browser")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("  1. Copy env_local_template.txt to .env.local and fill in your values")
        print("  2. Install dependencies: pip install -r requirements.txt")
        print("  3. Start PostgreSQL database")
        print("  4. Set up your OpenAI API key")
    
    print("=" * 60)

if __name__ == '__main__':
    main() 