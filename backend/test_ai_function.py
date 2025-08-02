#!/usr/bin/env python3
"""
Test AI function in email_ingestor_enhanced.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_ai_function():
    """Test the AI function directly"""
    try:
        from email_ingestor_enhanced import handle_email_via_openai
        
        print("🧪 Testing AI function...")
        
        # Test data
        subject = "Payment Receipt for BL-1234"
        body = "Hello, I have made the payment of $500 for BL-1234. Please confirm receipt."
        attachments = []
        from_addr = "test@example.com"
        
        print(f"📧 Subject: {subject}")
        print(f"📧 Body: {body}")
        print(f"📧 From: {from_addr}")
        
        # Call AI function
        result = handle_email_via_openai(subject, body, attachments, from_addr)
        
        print(f"🤖 AI Result: {result}")
        
        if result:
            print("✅ AI function working!")
            print(f"   Classification: {result.get('classification')}")
            print(f"   Confidence: {result.get('confidence_score')}")
            print(f"   Auto Send: {result.get('auto_send')}")
            print(f"   Custom Reply: {result.get('custom_reply', '')[:100]}...")
            return True
        else:
            print("❌ AI function returned None")
            return False
            
    except Exception as e:
        print(f"❌ Error testing AI function: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_openai_connection():
    """Test OpenAI connection"""
    try:
        import openai
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OpenAI API key not found in environment")
            return False
        
        print(f"🔑 OpenAI API key found: {api_key[:10]}...")
        
        # Test simple OpenAI call
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'Hello World'"}],
            max_tokens=10
        )
        
        print(f"✅ OpenAI connection working: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing AI functionality...")
    
    # Test OpenAI connection first
    if test_openai_connection():
        # Test AI function
        test_ai_function()
    else:
        print("❌ Cannot test AI function without OpenAI connection") 