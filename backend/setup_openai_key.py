#!/usr/bin/env python3
"""
Script to set up OpenAI API key for testing
"""

import os
import sys

def setup_openai_key():
    print("🔧 Setting up OpenAI API Key for Enhanced OCR Testing")
    print("=" * 60)
    
    # Check if .env.local exists
    env_file = ".env.local"
    if os.path.exists(env_file):
        print(f"✅ Found existing {env_file}")
        
        # Read current content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Check if OpenAI key is already set
        if "OPENAI_API_KEY=sk-" in content:
            print("✅ OpenAI API key is already configured!")
            return True
        else:
            print("⚠️  OpenAI API key not found in .env.local")
    else:
        print(f"❌ {env_file} not found")
        content = ""
    
    print("\n📝 To enable enhanced OCR testing, you need to:")
    print("1. Get an OpenAI API key from: https://platform.openai.com/api-keys")
    print("2. Add it to your .env.local file")
    print("3. Format: OPENAI_API_KEY=sk-your_actual_key_here")
    
    # Ask user for API key
    api_key = input("\n🔑 Enter your OpenAI API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("⏭️  Skipping OpenAI setup. Enhanced OCR will use fallback methods.")
        return False
    
    if not api_key.startswith("sk-"):
        print("❌ Invalid API key format. Should start with 'sk-'")
        return False
    
    # Add or update the API key in .env.local
    if "OPENAI_API_KEY=" in content:
        # Update existing key
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("OPENAI_API_KEY="):
                lines[i] = f"OPENAI_API_KEY={api_key}"
                break
        content = '\n'.join(lines)
    else:
        # Add new key
        if content and not content.endswith('\n'):
            content += '\n'
        content += f"OPENAI_API_KEY={api_key}\n"
    
    # Write back to file
    with open(env_file, 'w') as f:
        f.write(content)
    
    print(f"✅ OpenAI API key added to {env_file}")
    print("🔄 Please restart your Python session for changes to take effect")
    return True

if __name__ == "__main__":
    setup_openai_key() 