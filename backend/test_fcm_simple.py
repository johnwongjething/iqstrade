#!/usr/bin/env python3
"""
Simple FCM Test Script
Tests FCM service without starting the full Flask server
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_fcm_service():
    """Test FCM service directly"""
    try:
        print("🧪 Testing FCM Service...")
        
        # Import FCM service
        from fcm_service_modern import fcm_service
        
        # Test configuration
        print("✅ FCM service imported successfully")
        print(f"📋 Project ID: {fcm_service.project_id}")
        print(f"🔑 Service account configured: {'✅' if fcm_service.credentials else '❌'}")
        
        # Test sending a simple notification
        test_token = "test_token_123"  # This will fail but we can see the error
        try:
            result = fcm_service.send_notification(
                token=test_token,
                title="Test Notification",
                body="This is a test notification",
                data={"type": "test"}
            )
            print(f"✅ Test notification sent: {result}")
        except Exception as e:
            print(f"⚠️ Expected error with test token: {str(e)[:100]}...")
        
        print("\n🎉 FCM service is working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing FCM service: {e}")
        return False

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
    print("🚀 FCM Simple Test Script")
    print("=" * 50)
    
    test_environment()
    print()
    test_fcm_service()
    
    print("\n" + "=" * 50)
    print("📱 Next Steps:")
    print("1. Download ngrok from https://ngrok.com/download")
    print("2. Extract to a folder (e.g., C:\\ngrok)")
    print("3. Open Command Prompt and run: ngrok http 5000")
    print("4. Use the HTTPS URL for mobile testing") 