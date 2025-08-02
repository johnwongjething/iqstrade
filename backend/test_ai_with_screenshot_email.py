#!/usr/bin/env python3
"""
Test AI function with the exact email from the screenshot
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from email_ingestor_enhanced import handle_email_via_openai
import json

def test_screenshot_email():
    """Test with the exact email from the screenshot"""
    
    # Email details from screenshot
    subject = "ray"
    body = "Can you send me invoice and ctn number for BL NYC2201666"
    from_addr = "Jething John <johnwongjething@gmail.com>"
    attachments = []
    
    print("🧪 Testing AI function with screenshot email...")
    print(f"Subject: {subject}")
    print(f"From: {from_addr}")
    print(f"Body: {body}")
    print(f"Attachments: {len(attachments)}")
    print("-" * 50)
    
    try:
        result = handle_email_via_openai(subject, body, attachments, from_addr)
        
        print("✅ AI function completed successfully!")
        print("\n📊 Results:")
        print(f"Classification: {result.get('classification')}")
        print(f"Confidence Score: {result.get('confidence_score')}")
        print(f"Request Types: {result.get('request_types', [])}")
        print(f"BL Numbers: {result.get('bl_numbers', [])}")
        print(f"Valid BLs: {result.get('valid_bls', {})}")
        print(f"Invalid BLs: {result.get('invalid_bls', [])}")
        print(f"Auto Send: {result.get('auto_send')}")
        print(f"\n📝 Custom Reply:")
        print(result.get('custom_reply', 'No reply generated'))
        
    except Exception as e:
        print(f"❌ Error testing AI function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_screenshot_email() 