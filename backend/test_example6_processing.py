#!/usr/bin/env python3
"""
Test script to manually process Example 6 and check attachment handling
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
if not os.path.exists(env_file):
    env_file = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_file)

from email_ingestor import handle_email_via_openai
from db_utils import get_db_conn

def test_example6_processing():
    """Test processing Example 6 manually"""
    print("🧪 TESTING EXAMPLE 6 PROCESSING")
    print("=" * 50)
    
    # Example 6 data
    subject = "Fwd: 6 - PDF Payment Receipt"
    body = ""  # Empty body as per Example 6
    attachments = ["3.pdf"]  # The PDF attachment
    from_addr = "test@example.com"
    
    print(f"📧 Subject: {subject}")
    print(f"📧 Body: '{body}'")
    print(f"📧 Attachments: {attachments}")
    print(f"📧 From: {from_addr}")
    
    # Test the OpenAI processing
    print("\n🔄 Testing OpenAI processing...")
    try:
        result = handle_email_via_openai(subject, body, attachments, from_addr)
        print("✅ OpenAI processing completed")
        print(f"   Classification: {result.get('classification')}")
        print(f"   BL Numbers: {result.get('bl_numbers')}")
        print(f"   Paid Amount: {result.get('paid_amount')}")
        print(f"   Request Types: {result.get('request_types')}")
    except Exception as e:
        print(f"❌ OpenAI processing failed: {e}")
    
    # Check if 3.pdf exists
    pdf_path = "3.pdf"
    if os.path.exists(pdf_path):
        print(f"\n✅ Found {pdf_path}")
        print(f"   Size: {os.path.getsize(pdf_path)} bytes")
    else:
        print(f"\n❌ {pdf_path} not found")
    
    # Check downloads directory
    downloads_dir = "downloads"
    if os.path.exists(downloads_dir):
        files = os.listdir(downloads_dir)
        print(f"\n📁 Downloads directory contents:")
        for file in files:
            file_path = os.path.join(downloads_dir, file)
            size = os.path.getsize(file_path)
            print(f"   {file} ({size} bytes)")
    else:
        print(f"\n❌ Downloads directory not found")

if __name__ == "__main__":
    test_example6_processing() 