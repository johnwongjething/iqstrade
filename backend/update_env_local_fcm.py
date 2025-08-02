#!/usr/bin/env python3
"""
Update .env.local file with modern FCM environment variables
"""

import os
import re

def update_env_local():
    """Update .env.local file with FCM variables"""
    
    env_file = '.env.local'
    
    if not os.path.exists(env_file):
        print(f"❌ {env_file} not found!")
        return False
    
    # Read current content
    with open(env_file, 'r') as f:
        content = f.read()
    
    print(f"📝 Updating {env_file} with modern FCM variables...")
    
    # Remove old FCM variables if they exist
    old_fcm_pattern = r'# Add these to your \.env\.local file:\nOPENAI_REQUESTS_PER_MINUTE=.*?\nFIREBASE_WEB_PUSH_CERTIFICATE=.*?\n'
    content = re.sub(old_fcm_pattern, '', content, flags=re.DOTALL)
    
    # Add new FCM section
    new_fcm_section = '''# === FIREBASE CLOUD MESSAGING (FCM) - Modern OAuth 2.0 ===
# Service account file path (for OAuth 2.0 authentication)
GOOGLE_APPLICATION_CREDENTIALS=iqstrade-notifications-firebase-adminsdk-fbsvc-f52d11527b.json

# Firebase project configuration
FIREBASE_PROJECT_ID=iqstrade-notifications

# VAPID key for web push notifications
FIREBASE_WEB_PUSH_CERTIFICATE=BFwxgQkr7b5ScQrbsmlbiffWSQxzV051VhEw9tHaT8_yvwd3HBu7CmfUXxCKOsvbvKWT6ETb4A0ixJSIU81qOrw

# === OPENAI RATE LIMITING ===
OPENAI_REQUESTS_PER_MINUTE=60
OPENAI_REQUESTS_PER_HOUR=3500
EMAILS_PER_MINUTE=10
OPENAI_MAX_RETRIES=3
OPENAI_BASE_DELAY=1.0
OPENAI_MAX_DELAY=60.0

'''
    
    # Add the new section at the end
    content += '\n' + new_fcm_section
    
    # Write updated content
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ .env.local updated successfully!")
    print("📋 Added modern FCM variables:")
    print("   - GOOGLE_APPLICATION_CREDENTIALS")
    print("   - FIREBASE_PROJECT_ID")
    print("   - FIREBASE_WEB_PUSH_CERTIFICATE")
    print("   - Removed old FIREBASE_SERVER_KEY (no longer needed)")
    
    return True

if __name__ == "__main__":
    success = update_env_local()
    if success:
        print("\n🎉 .env.local is ready for modern FCM!")
        print("🚀 You can now test the FCM service locally")
    else:
        print("\n❌ Failed to update .env.local") 