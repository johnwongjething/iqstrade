#!/usr/bin/env python3
"""
Script to update all FCM imports from fcm_service_modern to fcm_service_fallback
"""

import os
import re

def update_file(file_path):
    """Update FCM imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update imports
        content = re.sub(
            r'from fcm_service_modern import fcm_service',
            'from fcm_service_fallback import fcm_service_fallback',
            content
        )
        
        # Update function calls
        content = re.sub(
            r'fcm_service\.send_notification\(',
            'fcm_service_fallback.send_notification(',
            content
        )
        
        content = re.sub(
            r'fcm_service\.send_to_topic\(',
            'fcm_service_fallback.send_to_topic(',
            content
        )
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Updated: {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Update all FCM imports in the backend directory"""
    files_to_update = [
        'email_ingestor.py',
        'email_ingestor_enhanced.py',
        'email_ingestor_working.py'
    ]
    
    updated_count = 0
    for file_path in files_to_update:
        if os.path.exists(file_path):
            if update_file(file_path):
                updated_count += 1
    
    print(f"\n🎉 Updated {updated_count}/{len(files_to_update)} files")

if __name__ == "__main__":
    main() 