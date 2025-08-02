#!/usr/bin/env python3
"""
Test BL Regex Pattern with Actual Database BL Numbers
"""

import re
from config import get_db_conn

def test_bl_regex():
    """Test the BL regex pattern with actual BL numbers"""
    
    # Get BL numbers from database
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT bl_number FROM bill_of_lading ORDER BY id LIMIT 20")
    db_bls = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    # The regex pattern used in email_ingestor.py
    expanded_bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})', re.IGNORECASE)
    
    print("🧪 Testing BL Regex Pattern")
    print("=" * 50)
    print(f"Pattern: {expanded_bl_pattern.pattern}")
    print()
    
    # Test with database BL numbers
    print("📊 Testing with Database BL Numbers:")
    print("-" * 30)
    
    for bl in db_bls:
        match = expanded_bl_pattern.search(bl)
        if match:
            print(f"✅ {bl} -> MATCH: {match.group(1)}")
        else:
            print(f"❌ {bl} -> NO MATCH")
    
    print()
    
    # Test with sample email text
    print("📧 Testing with Sample Email Text:")
    print("-" * 30)
    
    sample_texts = [
        "I paid $200 for BL-2024-001",
        "Please process BL-2024-002 payment",
        "What's the status of BL-2024-003?",
        "I need CTN for BL-2024-004 and BL-2024-005",
        "BL-2024-006 reserve settlement",
        "Multiple BLs: BL-2024-007, BL-2024-008, BL-2024-009"
    ]
    
    for text in sample_texts:
        matches = expanded_bl_pattern.findall(text)
        print(f"Text: {text}")
        print(f"Matches: {matches}")
        print()
    
    # Test with complex email
    print("📧 Testing with Complex Email:")
    print("-" * 30)
    
    complex_email = """Dear IQS Trade,

I need to make payments for multiple shipments:

1. BL-2024-001: USD 200 (full payment)
2. BL-2024-002: USD 170 (85% Allinpay)
3. BL-2024-003: USD 30 (15% reserve)

Please confirm receipt and send invoices. Also, what's the status of BL-2024-004?

Best regards,
Client"""
    
    matches = expanded_bl_pattern.findall(complex_email)
    print(f"Complex email matches: {matches}")
    
    # Check if all expected BLs are found
    expected_bls = ['BL-2024-001', 'BL-2024-002', 'BL-2024-003', 'BL-2024-004']
    found_bls = [match[1] if isinstance(match, tuple) else match for match in matches]
    
    print(f"\nExpected BLs: {expected_bls}")
    print(f"Found BLs: {found_bls}")
    
    missing_bls = set(expected_bls) - set(found_bls)
    if missing_bls:
        print(f"❌ Missing BLs: {missing_bls}")
    else:
        print("✅ All expected BLs found!")

if __name__ == "__main__":
    test_bl_regex() 