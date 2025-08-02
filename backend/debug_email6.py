#!/usr/bin/env python3
"""
Debug script for Email 6 BL extraction issue
"""

import os
import sys
import re
from unittest.mock import patch, Mock

def debug_email6():
    """Debug Email 6 BL extraction specifically"""
    
    # Set up environment variables for testing
    os.environ['OPENAI_API_KEY'] = 'test-key-for-mocking'
    
    print("🔍 Debugging Email 6 BL Extraction")
    print("=" * 50)
    
    # Email 6 data
    email6 = {
        "subject": "Fwd: 6", 
        "body": "", 
        "attachments": ["3.pdf"], 
        "from_addr": "johnwongjething@gmail.com"
    }
    
    # Mock PDF processing
    def mock_process_pdf(filepath):
        print(f"[MOCK] Processing PDF: {filepath}")
        if "3.pdf" in filepath:
            result = {
                "bl_number": "001-123, NYC220",
                "paid_amount": 420.0,
                "raw_text": "Payment for B/L 001-123, NYC220 Amount: $420 Ref: TEST987"
            }
            print(f"[MOCK] Returning: {result}")
            return result
        return {"raw_text": ""}
    
    # Mock database functions
    def mock_find_ctn_info(bl_numbers):
        print(f"[MOCK] find_ctn_info called with: {bl_numbers}")
        return [{"bl_number": bl, "ctn_number": f"CTN{bl}"} for bl in bl_numbers]
    
    def mock_find_invoice_info(bl_numbers):
        print(f"[MOCK] find_invoice_info called with: {bl_numbers}")
        return [{"bl_number": bl, "ctn_fee": 100.0, "service_fee": 50.0} for bl in bl_numbers]
    
    # Mock OpenAI
    def mock_openai(**kwargs):
        return Mock(
            choices=[Mock(message=Mock(content="Test reply"))]
        )
    
    # Test the BL extraction logic manually
    print("\n📋 Testing BL extraction logic manually:")
    
    # Simulate the PDF fields
    pdf_fields = {
        "bl_number": "001-123, NYC220",
        "paid_amount": 420.0,
        "raw_text": "Payment for B/L 001-123, NYC220 Amount: $420 Ref: TEST987"
    }
    
    print(f"PDF fields: {pdf_fields}")
    
    # Test the regex pattern
    expanded_bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})', re.IGNORECASE)
    
    # Test structured field extraction
    bl_val = pdf_fields.get('bl_number')
    print(f"\n🔍 Testing structured field: '{bl_val}'")
    
    if bl_val and isinstance(bl_val, str):
        # Split by comma
        bls = [b.strip() for b in re.split(r'[\s,;/]+', bl_val) if b.strip()]
        print(f"Split BLs: {bls}")
        
        # Apply regex
        regex_bls = expanded_bl_pattern.findall(bl_val)
        print(f"Regex BLs: {regex_bls}")
    
    # Test raw text extraction
    raw_text = pdf_fields.get('raw_text')
    print(f"\n🔍 Testing raw text: '{raw_text}'")
    
    if raw_text:
        raw_bls = expanded_bl_pattern.findall(raw_text)
        print(f"Raw text BLs: {raw_bls}")
    
    # Now test with the actual function
    print("\n🧪 Testing with actual handle_email_via_openai function:")
    
    with patch('email_ingestor.find_ctn_info', side_effect=mock_find_ctn_info), \
         patch('email_ingestor.find_invoice_info', side_effect=mock_find_invoice_info), \
         patch('email_ingestor.process_pdf', side_effect=mock_process_pdf), \
         patch('openai.chat.completions.create', side_effect=mock_openai), \
         patch('email_ingestor.save_draft_reply'), \
         patch('email_ingestor.process_payment_receipt_email'):
        
        try:
            from email_ingestor import handle_email_via_openai
            
            result = handle_email_via_openai(
                email6['subject'], 
                email6['body'], 
                email6['attachments'], 
                email6['from_addr']
            )
            
            print(f"\n✅ Result:")
            print(f"   BLs extracted: {result.get('bl_numbers', [])}")
            print(f"   Valid BLs: {list(result.get('bl_payment_map', {}).keys())}")
            print(f"   Paid amount: {result.get('paid_amount', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_email6() 