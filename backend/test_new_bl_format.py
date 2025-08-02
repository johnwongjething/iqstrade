#!/usr/bin/env python3
"""
Test New BL Number Format with Regex Pattern
"""

import re

def test_new_bl_format():
    """Test the regex pattern with new BL number format"""
    
    # The regex pattern from email_ingestor.py
    expanded_bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})', re.IGNORECASE)
    
    print("🧪 Testing New BL Number Format")
    print("=" * 50)
    print(f"Pattern: {expanded_bl_pattern.pattern}")
    print()
    
    # Test with new BL number format (BL2024001)
    new_bl_numbers = [
        'BL2024001', 'BL2024002', 'BL2024003', 'BL2024004', 'BL2024005',
        'BL2024006', 'BL2024007', 'BL2024008', 'BL2024009', 'BL2024010'
    ]
    
    print("📊 Testing with New BL Numbers (BL2024XXX format):")
    print("-" * 50)
    
    for bl in new_bl_numbers:
        match = expanded_bl_pattern.search(bl)
        if match:
            print(f"✅ {bl} -> MATCH: {match.group(1)}")
        else:
            print(f"❌ {bl} -> NO MATCH")
    
    print()
    
    # Test with sample email text using new format
    print("📧 Testing with Sample Email Text (New Format):")
    print("-" * 50)
    
    sample_texts = [
        "I paid $200 for BL2024001",
        "Please process BL2024002 payment",
        "What's the status of BL2024003?",
        "I need CTN for BL2024004 and BL2024005",
        "BL2024006 reserve settlement",
        "Multiple BLs: BL2024007, BL2024008, BL2024009"
    ]
    
    for text in sample_texts:
        matches = expanded_bl_pattern.findall(text)
        print(f"Text: {text}")
        print(f"Matches: {matches}")
        print()
    
    # Test with complex email using new format
    print("📧 Testing with Complex Email (New Format):")
    print("-" * 50)
    
    complex_email = """Dear IQS Trade,

I need to make payments for multiple shipments:

1. BL2024001: USD 200 (full payment)
2. BL2024002: USD 170 (85% Allinpay)
3. BL2024003: USD 30 (15% reserve)

Please confirm receipt and send invoices. Also, what's the status of BL2024004?

Best regards,
Client"""
    
    matches = expanded_bl_pattern.findall(complex_email)
    print(f"Complex email matches: {matches}")
    
    # Check if all expected BLs are found
    expected_bls = ['BL2024001', 'BL2024002', 'BL2024003', 'BL2024004']
    found_bls = [match[1] if isinstance(match, tuple) else match for match in matches]
    
    print(f"\nExpected BLs: {expected_bls}")
    print(f"Found BLs: {found_bls}")
    
    missing_bls = set(expected_bls) - set(found_bls)
    if missing_bls:
        print(f"❌ Missing BLs: {missing_bls}")
    else:
        print("✅ All expected BLs found!")

if __name__ == "__main__":
    test_new_bl_format() 