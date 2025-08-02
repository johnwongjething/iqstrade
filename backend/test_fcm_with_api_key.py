#!/usr/bin/env python3
"""
Test FCM with API key as server key
"""

import requests
import json

def test_fcm_with_api_key():
    """Test FCM using API key as server key"""
    
    # Your API key from Firebase config
    api_key = "AIzaSyBqEvEzPZNbvrDeW8k8iL2UW54hij9lODQ"
    
    # Test payload
    payload = {
        'to': '/topics/test',
        'notification': {
            'title': '🧪 Test Notification',
            'body': 'Testing FCM with API key',
            'icon': '/favicon.ico'
        },
        'data': {
            'type': 'test',
            'message': 'This is a test notification'
        }
    }
    
    headers = {
        'Authorization': f'key={api_key}',
        'Content-Type': 'application/json'
    }
    
    print("🧪 Testing FCM with API Key...")
    print(f"API Key: {api_key[:20]}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            'https://fcm.googleapis.com/fcm/send',
            json=payload,
            headers=headers
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response: {json.dumps(result, indent=2)}")
            
            if result.get('success') == 1:
                print("🎉 API Key works as server key!")
                return True
            else:
                print("❌ API Key doesn't work as server key")
                print(f"Error: {result.get('results', [{}])[0].get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_fcm_with_api_key()
    
    if success:
        print("\n🎉 SUCCESS! You can use your API key as the server key.")
        print("Add this to your environment variables:")
        print("FIREBASE_SERVER_KEY=AIzaSyBqEvEzPZNbvrDeW8k8iL2UW54hij9lODQ")
    else:
        print("\n❌ API key doesn't work as server key.")
        print("You'll need to find the actual server key using the methods shown earlier.") 