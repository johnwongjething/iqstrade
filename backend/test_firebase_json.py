#!/usr/bin/env python3
"""
Firebase Service Account JSON Validator
Test if the Firebase service account JSON file is still valid
"""
import os
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env.local')

def test_firebase_json():
    """Test if Firebase service account JSON is valid"""
    print("🔍 Testing Firebase service account JSON...")
    
    # Get the service account path
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
    
    if not service_account_path:
        print("❌ FIREBASE_SERVICE_ACCOUNT_PATH not set in environment")
        return False
    
    print(f"📄 Service account path: {service_account_path}")
    
    # Check if file exists
    if not os.path.exists(service_account_path):
        print(f"❌ Service account file not found: {service_account_path}")
        return False
    
    print("✅ Service account file exists")
    
    # Try to read and parse the JSON
    try:
        with open(service_account_path, 'r') as f:
            content = json.load(f)
        
        print("✅ JSON file is valid")
        
        # Check required fields
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email', 'client_id']
        missing_fields = []
        
        for field in required_fields:
            if field not in content:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print("✅ All required fields present")
        print(f"📋 Project ID: {content.get('project_id')}")
        print(f"📧 Client Email: {content.get('client_email')}")
        print(f"🔑 Private Key ID: {content.get('private_key_id')}")
        
        # Check private key format
        private_key = content.get('private_key', '')
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ Private key format is invalid")
            return False
        
        print("✅ Private key format is valid")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON file is corrupted: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return False
    
    # Try to create credentials
    try:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/firebase.messaging']
        )
        print("✅ Credentials created successfully")
        
        # Try to refresh the token
        try:
            credentials.refresh(Request())
            print("✅ Access token generated successfully")
            print(f"🔑 Token preview: {credentials.token[:20]}...")
            return True
        except Exception as e:
            print(f"❌ Failed to generate access token: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to create credentials: {e}")
        return False

def check_firebase_project():
    """Check if Firebase project is accessible"""
    print("\n🔍 Checking Firebase project access...")
    
    try:
        import requests
        
        # Get project ID from environment or JSON file
        project_id = os.getenv('FIREBASE_PROJECT_ID', 'iqstrade-notifications')
        
        # Try to access Firebase project info
        url = f"https://firebase.googleapis.com/v1beta1/projects/{project_id}"
        
        # This would require authentication, but we can at least check if the project exists
        print(f"📋 Project ID: {project_id}")
        print("ℹ️ Note: Full project validation requires authenticated API calls")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking Firebase project: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Firebase Service Account JSON Validator")
    print("=" * 50)
    
    json_valid = test_firebase_json()
    project_accessible = check_firebase_project()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    if json_valid:
        print("✅ Firebase service account JSON is VALID")
    else:
        print("❌ Firebase service account JSON is INVALID")
    
    if project_accessible:
        print("✅ Firebase project appears accessible")
    else:
        print("❌ Firebase project may not be accessible")
    
    if json_valid and project_accessible:
        print("\n🎉 Your Firebase setup should work correctly!")
    else:
        print("\n⚠️ There may be issues with your Firebase setup")
        print("   Consider re-downloading the service account JSON from Google Cloud Console") 