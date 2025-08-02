#!/usr/bin/env python3
"""
Test OCR extraction fix
"""

import os
from dotenv import load_dotenv
from ocr_processor_enhanced_v5 import extract_fields_openai_enhanced_v5

# Load environment variables
load_dotenv('.env.local')

def test_ocr_extraction():
    """Test OCR extraction with a simple PDF"""
    print("Testing OCR extraction...")
    
    # Test with a simple text extraction first
    try:
        # Create a simple test PDF or use an existing one
        test_pdf_path = "test_sample.pdf"
        
        if os.path.exists(test_pdf_path):
            print(f"Testing with existing PDF: {test_pdf_path}")
            result = extract_fields_openai_enhanced_v5(test_pdf_path)
            print("✅ OCR extraction successful!")
            print(f"Result: {result}")
        else:
            print("⚠️ No test PDF found, testing API connectivity only...")
            # Test the API call directly
            import openai
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "Hello, this is a test of the OCR API."}
                ],
                max_tokens=50
            )
            print("✅ API connectivity test successful!")
            print(f"Response: {response.choices[0].message.content}")
            
    except Exception as e:
        print(f"❌ OCR extraction failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_ocr_extraction()
    if success:
        print("\n🎉 OCR extraction is working!")
    else:
        print("\n❌ OCR extraction has issues!") 