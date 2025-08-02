#!/usr/bin/env python3
"""
Test script to verify 3.pdf processing
"""

import os
from ocr_processor import process_pdf

def test_3pdf():
    """Test processing of 3.pdf file"""
    
    pdf_path = "3.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File {pdf_path} not found!")
        return
    
    print(f"🧪 Testing 3.pdf processing")
    print("=" * 40)
    print(f"File: {pdf_path}")
    print(f"Size: {os.path.getsize(pdf_path)} bytes")
    print()
    
    try:
        # Process the PDF
        print("📄 Processing PDF...")
        result = process_pdf(pdf_path)
        
        print("✅ PDF processed successfully!")
        print("\n📋 Extracted Data:")
        print(f"Document Type: {result.get('document_type', 'N/A')}")
        print(f"BL Number: {result.get('bl_number', 'N/A')}")
        print(f"Paid Amount: {result.get('paid_amount', 'N/A')}")
        print(f"Raw Text: {result.get('raw_text', 'N/A')[:200]}...")
        
        # Test BL extraction
        import re
        bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})', re.IGNORECASE)
        
        raw_text = result.get('raw_text', '')
        bls_found = bl_pattern.findall(raw_text)
        print(f"\n🔍 BLs found in raw text: {bls_found}")
        
        # Test payment amount extraction
        payment_patterns = [
            r'\$\s?([0-9]+(?:\.[0-9]{1,2})?)',
            r'USD\s*([0-9]+(?:\.[0-9]{1,2})?)',
            r'Amount[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
        ]
        
        amounts_found = []
        for pattern in payment_patterns:
            matches = re.findall(pattern, raw_text, re.IGNORECASE)
            amounts_found.extend(matches)
        
        print(f"💰 Payment amounts found: {amounts_found}")
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_3pdf() 