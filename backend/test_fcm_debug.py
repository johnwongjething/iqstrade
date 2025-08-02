#!/usr/bin/env python3
"""
FCM Debug Test Script
Tests FCM functionality step by step
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
        
        return fcm_service
        
    except Exception as e:
        print(f"❌ Error testing FCM service: {e}")
        return None

def test_backend_endpoints():
    """Test backend endpoints"""
    print("\n🌐 Testing Backend Endpoints...")
    
    base_url = "http://localhost:5000"
    endpoints = [
        ("/test", "GET"),
        ("/api/fcm/test-simple", "GET"),
        ("/api/fcm/token/public", "POST"),
        ("/api/fcm/test/public", "POST")
    ]
    
    for endpoint, method in endpoints:
        try:
            url = base_url + endpoint
            if method == "POST":
                if "token" in endpoint:
                    response = requests.post(url, json={"token": "test_token_123"})
                else:
                    response = requests.post(url, json={})
            else:
                response = requests.get(url)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} ({method}): Working")
                if method == "POST":
                    try:
                        data = response.json()
                        print(f"   Response: {data}")
                    except:
                        print(f"   Response: {response.text[:100]}...")
            else:
                print(f"⚠️ {endpoint} ({method}): Status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} ({method}): Connection failed (backend not running)")
        except Exception as e:
            print(f"❌ {endpoint} ({method}): Error - {str(e)[:50]}...")

def test_fcm_notification_sending():
    """Test sending a real FCM notification"""
    print("\n📱 Testing FCM Notification Sending...")
    
    fcm_service = test_fcm_service()
    if not fcm_service:
        print("❌ FCM service not available")
        return
    
    # Test with a dummy token (this will fail but we can see the error)
    test_token = "test_token_123"
    
    try:
        result = fcm_service.send_notification(
            token=test_token,
            title="Test Notification",
            body="This is a test notification from debug script",
            data={"type": "test", "debug": "true"}
        )
        print(f"✅ Test notification sent: {result}")
    except Exception as e:
        print(f"⚠️ Expected error with test token: {str(e)[:100]}...")
        
        # Check if it's a token format error (which is expected)
        if "Invalid registration token" in str(e) or "NotRegistered" in str(e):
            print("✅ FCM service is working correctly - token format error is expected")
        else:
            print(f"❌ Unexpected error: {e}")

def test_environment():
    """Test environment variables"""
    print("🔧 Testing Environment Variables...")
    
    required_vars = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'FIREBASE_PROJECT_ID',
        'FIREBASE_WEB_PUSH_CERTIFICATE'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:20]}..." if len(value) > 20 else f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    # Check if service account file exists
    creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if creds_file and os.path.exists(creds_file):
        print(f"✅ Service account file exists: {creds_file}")
    else:
        print(f"❌ Service account file not found: {creds_file}")

if __name__ == '__main__':
    print("🚀 FCM Debug Test Script")
    print("=" * 50)
    
    test_environment()
    test_backend_endpoints()
    test_fcm_notification_sending()
    
    print("\n" + "=" * 50)
    print("📋 Next Steps:")
    print("1. Check phone browser console for FCM token")
    print("2. Verify notification permissions are allowed")
    print("3. Test with a real FCM token from your phone") 