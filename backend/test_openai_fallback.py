#!/usr/bin/env python3
"""
Test script to verify OpenAI fallback functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))
if not os.path.exists(os.path.join(os.path.dirname(__file__), '.env.local')):
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

import openai
openai.api_key = os.getenv('OPENAI_API_KEY')

def test_openai_fallback():
    """Test the OpenAI fallback functionality"""
    
    if not openai.api_key:
        print("❌ No OpenAI API key found. Please set OPENAI_API_KEY in your .env file.")
        return
    
    print("🧪 Testing OpenAI Fallback Functionality")
    print("=" * 50)
    
    # Import the fallback function from email_ingestor
    from email_ingestor import openai_call_with_fallback
    
    # Test message
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello from GPT-4o or GPT-3.5-turbo' and tell me which model you are."}
    ]
    
    try:
        print("📤 Making OpenAI API call...")
        response = openai_call_with_fallback(test_messages, temperature=0)
        print(f"✅ Success! Response: {response}")
        
        # Check which model was used
        if "gpt-4o" in response.lower():
            print("🎯 Used GPT-4o")
        elif "gpt-3.5" in response.lower():
            print("🎯 Used GPT-3.5-turbo (fallback)")
        else:
            print("🎯 Model not specified in response")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 This might be due to:")
        print("1. Invalid API key")
        print("2. No API credits")
        print("3. Network issues")
        print("4. Rate limiting")

if __name__ == "__main__":
    test_openai_fallback() 