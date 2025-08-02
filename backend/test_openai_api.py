#!/usr/bin/env python3
"""
Test OpenAI API functionality
"""

import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Set API key
openai.api_key = os.getenv('OPENAI_API_KEY')

def test_openai_api():
    """Test if OpenAI API is working"""
    print("Testing OpenAI API...")
    
    try:
        # Test the old API format
        print("Testing old API format (openai.ChatCompletion.create)...")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, please respond with 'API is working'"}
            ],
            max_tokens=50
        )
        print(f"✅ Old API format works: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ New API format failed: {e}")
        return False
    
    try:
        # Test the new API format (should fail)
        print("Testing new API format (openai.chat.completions.create)...")
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello"}
            ]
        )
        print(f"⚠️ New API format still works: {response.choices[0].message.content}")
    except Exception as e:
        print(f"✅ New API format correctly failed: {e}")
    
    return True

if __name__ == "__main__":
    success = test_openai_api()
    if success:
        print("\n🎉 OpenAI API is working correctly!")
    else:
        print("\n❌ OpenAI API has issues!") 