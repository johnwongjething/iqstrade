#!/usr/bin/env python3
"""
Test script to check BL regex pattern
"""

import re

def test_bl_regex():
    """Test the BL regex pattern with sample text"""
    
    # The regex pattern from email_ingestor.py
    expanded_bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})', re.IGNORECASE)
    
    # Sample text from the PDF
    sample_text = "Payment for B/L  001-123, NYC220\nAmount: $420\nRef: TEST987"
    
    print("🧪 Testing BL Regex Pattern")
    print("=" * 40)
    print(f"Pattern: {expanded_bl_pattern.pattern}")
    print(f"Sample text: {sample_text}")
    print()
    
    # Test the regex
    matches = expanded_bl_pattern.findall(sample_text)
    print(f"🔍 Matches found: {matches}")
    
    # Test individual BL numbers
    test_bls = ["001-123", "NYC220", "TEST987"]
    print("\n📋 Testing individual BL numbers:")
    for bl in test_bls:
        match = expanded_bl_pattern.search(bl)
        if match:
            print(f"  ✅ '{bl}' -> MATCH: {match.group(0)}")
        else:
            print(f"  ❌ '{bl}' -> NO MATCH")
    
    # Test with B/L prefix
    test_with_prefix = ["B/L 001-123", "BL NYC220", "B/L TEST987"]
    print("\n📋 Testing with B/L prefix:")
    for bl in test_with_prefix:
        match = expanded_bl_pattern.search(bl)
        if match:
            print(f"  ✅ '{bl}' -> MATCH: {match.group(0)}")
        else:
            print(f"  ❌ '{bl}' -> NO MATCH")

if __name__ == "__main__":
    test_bl_regex() 