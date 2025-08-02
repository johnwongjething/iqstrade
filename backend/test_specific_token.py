#!/usr/bin/env python3
"""
Test sending notification to specific FCM token
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_specific_token():
    """Test sending notification to the user's specific token"""
    
    # The token from the user's phone
    user_token = "cAN0cMuke4CBHvZHD2VEgm:APA91bHvZHD2VEgm..."  # Add the full token here
    
    try:
        print("🧪 Testing FCM Service with specific token...")
        
        # Import FCM service
        from fcm_service_modern import fcm_service
        
        print("✅ FCM service imported successfully")
        print(f"📋 Project ID: {fcm_service.project_id}")
        
        # Send notification to specific token
        print(f"📱 Sending notification to token: {user_token[:20]}...")
        
        result = fcm_service.send_notification(
            token=user_token,
            title="Direct Test Notification",
            body="This is a direct test to your specific FCM token!",
            data={"type": "direct_test", "timestamp": "2025-07-31"}
        )
        
        print(f"✅ Notification sent successfully: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        
        # Check for specific error types
        if "Invalid registration token" in str(e):
            print("❌ Token format is invalid")
        elif "NotRegistered" in str(e):
            print("❌ Token is not registered with FCM")
        elif "Unregistered" in str(e):
            print("❌ Token has been unregistered")
        else:
            print(f"❌ Other error: {e}")
        
        return False

if __name__ == '__main__':
    print("🚀 Testing Specific FCM Token")
    print("=" * 50)
    
    # Ask user to input the full token
    print("Please paste your full FCM token from the phone:")
    user_input = input("Token: ").strip()
    
    if user_input:
        # Update the token in the function
        import re
        with open(__file__, 'r') as f:
            content = f.read()
        
        # Replace the placeholder token
        updated_content = re.sub(
            r'user_token = "cAN0cMuke4CBHvZHD2VEgm:APA91bHvZHD2VEgm\.\.\."',
            f'user_token = "{user_input}"',
            content
        )
        
        with open(__file__, 'w') as f:
            f.write(updated_content)
        
        print("✅ Token updated, now testing...")
        test_specific_token()
    else:
        print("❌ No token provided") 