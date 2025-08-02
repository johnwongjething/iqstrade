#!/usr/bin/env python3
"""
Helper script to get FCM server key from service account JSON
"""

import json
import os

def get_server_key_from_service_account():
    """Extract server key from service account JSON file"""
    
    # Path to your service account JSON file
    service_account_path = "iqstrade-notifications-firebase-adminsdk-fbsvc-f52d11527b.json"
    
    if not os.path.exists(service_account_path):
        print(f"❌ Service account file not found: {service_account_path}")
        print("Please make sure the JSON file is in the current directory")
        return None
    
    try:
        with open(service_account_path, 'r') as f:
            service_account = json.load(f)
        
        print("✅ Service account JSON loaded successfully")
        print(f"Project ID: {service_account.get('project_id')}")
        print(f"Client Email: {service_account.get('client_email')}")
        
        # For FCM, we need to get the server key from Firebase Console
        # The service account JSON doesn't contain the server key directly
        print("\n📋 Next Steps:")
        print("1. Go to Firebase Console → Project Settings → Cloud Messaging")
        print("2. Look for 'Server key' in the 'Project credentials' section")
        print("3. Copy the server key (starts with 'AIza...')")
        print("4. Add it to your environment variables as FIREBASE_SERVER_KEY")
        
        return service_account
        
    except Exception as e:
        print(f"❌ Error reading service account file: {e}")
        return None

if __name__ == "__main__":
    get_server_key_from_service_account() 