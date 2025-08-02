#!/usr/bin/env python3
"""
Check if FIREBASE_SERVER_KEY is available
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def check_server_key():
    """Check if FIREBASE_SERVER_KEY is set"""
    
    print("🔍 Checking FIREBASE_SERVER_KEY")
    print("=" * 40)
    
    server_key = os.getenv('FIREBASE_SERVER_KEY')
    
    if server_key:
        print(f"✅ FIREBASE_SERVER_KEY found: {server_key[:20]}...")
        return True
    else:
        print("❌ FIREBASE_SERVER_KEY not found")
        print("\n📋 To get your FIREBASE_SERVER_KEY:")
        print("1. Go to Firebase Console")
        print("2. Select your project")
        print("3. Go to Project Settings")
        print("4. Go to Cloud Messaging tab")
        print("5. Copy the 'Server key'")
        print("6. Add it to your .env.local file:")
        print("   FIREBASE_SERVER_KEY=your_server_key_here")
        return False

if __name__ == '__main__':
    check_server_key() 