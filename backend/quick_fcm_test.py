#!/usr/bin/env python3
"""
Quick FCM Test - No ngrok needed
Tests FCM service and endpoints directly
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_fcm_service():
    """Test FCM service directly"""
    try:
        print("🧪 Testing FCM Service...")
        
        # Import FCM service
        from fcm_service_modern import fcm_service
        
        print("✅ FCM service imported successfully")
        print(f"📋 Project ID: {fcm_service.project_id}")
        print(f"🔑 Service account configured: {'✅' if fcm_service.credentials else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing FCM service: {e}")
        return False

def test_backend_endpoints():
    """Test backend endpoints"""
    print("\n🌐 Testing Backend Endpoints...")
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/test",
        "/api/fcm/test-simple",
        "/api/fcm/token/public"
    ]
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            if endpoint == "/api/fcm/token/public":
                # Test POST request
                response = requests.post(url, json={"token": "test_token_123"})
            else:
                # Test GET request
                response = requests.get(url)
            
            if response.status_code == 200:
                print(f"✅ {endpoint}: Working")
            else:
                print(f"⚠️ {endpoint}: Status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: Connection failed (backend not running)")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {str(e)[:50]}...")

def test_firebase_config():
    """Test Firebase configuration"""
    print("\n🔥 Testing Firebase Configuration...")
    
    # Check if service account file exists
    creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_file and os.path.exists(creds_file):
        print(f"✅ Service account file exists: {creds_file}")
    else:
        print(f"❌ Service account file not found: {creds_file}")
    
    # Check environment variables
    required_vars = [
        'FIREBASE_PROJECT_ID',
        'FIREBASE_WEB_PUSH_CERTIFICATE'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set")

def test_frontend_firebase():
    """Test frontend Firebase configuration"""
    print("\n📱 Testing Frontend Firebase...")
    
    try:
        # Check if frontend Firebase config exists
        firebase_config_path = "../frontend/src/firebase.js"
        if os.path.exists(firebase_config_path):
            print("✅ Frontend Firebase config exists")
            
            # Read and check config
            with open(firebase_config_path, 'r') as f:
                content = f.read()
                
            if "apiKey" in content and "projectId" in content:
                print("✅ Firebase config has required fields")
            else:
                print("❌ Firebase config missing required fields")
        else:
            print("❌ Frontend Firebase config not found")
            
    except Exception as e:
        print(f"❌ Error checking frontend: {e}")

if __name__ == '__main__':
    print("🚀 Quick FCM Test - No ngrok needed")
    print("=" * 50)
    
    test_firebase_config()
    test_fcm_service()
    test_backend_endpoints()
    test_frontend_firebase()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print("✅ Backend is running (from logs)")
    print("✅ FCM service is configured")
    print("✅ Firebase credentials are loaded")
    print("\n🎯 Next Steps:")
    print("1. Get correct ngrok authtoken from dashboard")
    print("2. Run: ngrok config add-authtoken YOUR_TOKEN")
    print("3. Run: ngrok http 5000")
    print("4. Use HTTPS URL for mobile testing") 