#!/usr/bin/env python3
"""
Debug container number extraction from BOL documents
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

def debug_container_extraction():
    """Debug container number extraction"""
    
    print("🔍 DEBUGGING CONTAINER EXTRACTION")
    print("=" * 40)
    
    # Test with BOL documents that should have container numbers
    test_files = [
        "New folder (2)/BILL1.pdf",
        "New folder (2)/BILL2.pdf", 
        "New folder (2)/BILL3.pdf",
        "New folder (2)/BILL4.pdf",
        "New folder (2)/BILL5.pdf",
        "New folder (2)/BILL6.pdf"
    ]
    
    for pdf_path in test_files:
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            continue
            
        print(f"\n📄 Testing: {pdf_path}")
        print("-" * 30)
        
        try:
            # Test basic OCR extraction first
            print("🔍 Testing basic OCR extraction...")
            
            # Try OpenAI extraction
            try:
                from ocr_processor import extract_fields_openai
                basic_fields_openai = extract_fields_openai(pdf_path)
                print(f"   ✅ OpenAI extraction successful")
                print(f"   Container Numbers (OpenAI): {basic_fields_openai.get('container_numbers', 'MISSING')}")
                print(f"   Raw Text Length: {len(basic_fields_openai.get('raw_text', ''))}")
            except Exception as e:
                print(f"   ❌ OpenAI extraction failed: {e}")
                basic_fields_openai = {}
            
            # Try Google Vision extraction
            try:
                from extract_fields import extract_fields as extract_fields_legacy
                basic_fields_legacy = extract_fields_legacy(pdf_path)
                print(f"   ✅ Google Vision extraction successful")
                print(f"   Container Numbers (Google): {basic_fields_legacy.get('container_numbers', 'MISSING')}")
                print(f"   Raw Text Length: {len(basic_fields_legacy.get('raw_text', ''))}")
            except Exception as e:
                print(f"   ❌ Google Vision extraction failed: {e}")
                basic_fields_legacy = {}
            
            # Test enhanced OCR
            print("\n🔍 Testing enhanced OCR...")
            try:
                from enhanced_ocr_processor import extract_fields_enhanced
                
                # Test for user ray40 (use_openai=True)
                result_openai = extract_fields_enhanced(pdf_path, use_openai=True)
                print(f"   ✅ Enhanced OCR (OpenAI) successful")
                print(f"   Container Numbers: {result_openai.get('container_numbers', 'MISSING')}")
                print(f"   Container Count: {result_openai.get('container_count', 'MISSING')}")
                print(f"   Shipment Type: {result_openai.get('shipment_type', 'MISSING')}")
                print(f"   CTN Fee: ${result_openai.get('calculated_ctn_fee', 'MISSING')}")
                print(f"   Service Fee: ${result_openai.get('calculated_service_fee', 'MISSING')}")
                
                # Test for other users (use_openai=False)
                result_legacy = extract_fields_enhanced(pdf_path, use_openai=False)
                print(f"   ✅ Enhanced OCR (Google Vision) successful")
                print(f"   Container Numbers: {result_legacy.get('container_numbers', 'MISSING')}")
                print(f"   Container Count: {result_legacy.get('container_count', 'MISSING')}")
                print(f"   Shipment Type: {result_legacy.get('shipment_type', 'MISSING')}")
                print(f"   CTN Fee: ${result_legacy.get('calculated_ctn_fee', 'MISSING')}")
                print(f"   Service Fee: ${result_legacy.get('calculated_service_fee', 'MISSING')}")
                
            except Exception as e:
                print(f"   ❌ Enhanced OCR failed: {e}")
                import traceback
                traceback.print_exc()
            
            # Show raw text sample for debugging
            if basic_fields_openai.get('raw_text'):
                print(f"\n📝 Raw Text Sample (first 500 chars):")
                raw_text = basic_fields_openai.get('raw_text', '')[:500]
                print(f"   {raw_text}...")
                
                # Look for container patterns in raw text
                import re
                container_patterns = [
                    r'\b[A-Z]{4}\d{7}\b',  # Standard container format
                    r'CONTR\s*#\s*([A-Z0-9]+)',
                    r'CONTAINER\s*#\s*([A-Z0-9]+)',
                    r'CONT\s*#\s*([A-Z0-9]+)'
                ]
                
                print(f"\n🔍 Container patterns found in raw text:")
                for pattern in container_patterns:
                    matches = re.findall(pattern, raw_text, re.IGNORECASE)
                    if matches:
                        print(f"   Pattern '{pattern}': {matches}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_container_extraction() 