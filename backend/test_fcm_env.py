#!/usr/bin/env python3
"""
Test FCM Environment Variables
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_fcm_environment():
    """Test if FCM environment variables are set correctly"""
    
    print("🔍 Testing FCM Environment Variables")
    print("=" * 50)
    
    # Check required environment variables
    required_vars = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'FIREBASE_PROJECT_ID', 
        'FIREBASE_WEB_PUSH_CERTIFICATE'
    ]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:50]}{'...' if len(value) > 50 else ''}")
        else:
            print(f"❌ {var}: NOT SET")
            all_good = False
    
    # Check if service account file exists
    service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if service_account_path:
        if os.path.exists(service_account_path):
            print(f"✅ Service account file exists: {service_account_path}")
        else:
            print(f"❌ Service account file NOT FOUND: {service_account_path}")
            all_good = False
    
    # Test FCM service initialization
    print("\n🧪 Testing FCM Service Initialization")
    print("-" * 40)
    
    try:
        from fcm_service_modern import FCMService
        fcm_service = FCMService()
        
        if fcm_service.credentials:
            print("✅ FCM Service initialized successfully")
            print(f"✅ Project ID: {fcm_service.project_id}")
            print(f"✅ Access token: {fcm_service.access_token[:20] if fcm_service.access_token else 'None'}...")
        else:
            print("❌ FCM Service failed to initialize")
            all_good = False
            
    except Exception as e:
        print(f"❌ Error initializing FCM Service: {e}")
        all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All FCM environment variables are set correctly!")
        print("✅ FCM should work properly")
    else:
        print("❌ Some FCM environment variables are missing or incorrect")
        print("📋 Please check your .env.local file")
    
    return all_good

if __name__ == '__main__':
    test_fcm_environment() 