#!/usr/bin/env python3
"""
Script to help find Firebase server key
"""

def find_server_key_instructions():
    """Provide instructions for finding the server key"""
    
    print("🔍 Firebase Server Key Search Instructions")
    print("=" * 50)
    
    print("\n📋 Method 1: Check Cloud Messaging Tab")
    print("1. Go to Firebase Console → Project Settings → Cloud Messaging")
    print("2. Look for 'Server key' in 'Project credentials' section")
    print("3. If not found, try Method 2")
    
    print("\n📋 Method 2: Check Legacy API")
    print("1. Go to Firebase Console → Project Settings → Service accounts")
    print("2. Look for 'Firebase Admin SDK' section")
    print("3. Check if there's a 'Legacy server key' option")
    
    print("\n📋 Method 3: Google Cloud Console")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Select your project: iqstrade-notifications")
    print("3. Go to APIs & Services → Credentials")
    print("4. Look for 'API keys' or 'Server keys'")
    
    print("\n📋 Method 4: Use API Key Instead")
    print("1. In Firebase Console → Project Settings → General")
    print("2. Copy the 'Web API Key' (starts with AIza...)")
    print("3. This might work as a server key for FCM")
    
    print("\n📋 Method 5: Create New Server Key")
    print("1. Go to Google Cloud Console")
    print("2. APIs & Services → Credentials")
    print("3. Click 'Create Credentials' → 'API Key'")
    print("4. Restrict it to Firebase Cloud Messaging API")
    
    print("\n💡 Alternative: Test with API Key")
    print("The Web API Key from Firebase might work as a server key.")
    print("Let's try using your existing API key: AIzaSyBqEvEzPZNbvrDeW8k8iL2UW54hij9lODQ")

if __name__ == "__main__":
    find_server_key_instructions() 