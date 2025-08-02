#!/usr/bin/env python3
"""
Script to manually fix BL numbers for existing emails
"""

import re
from config import get_db_conn

def extract_bl_numbers_from_text(text):
    """Extract BL numbers from text using the same pattern as email_ingestor.py"""
    if not text:
        return []
    
    # Same pattern as in email_ingestor.py
    bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})', re.IGNORECASE)
    
    # Also try a more specific pattern for "BL" followed by numbers
    bl_specific_pattern = re.compile(r'BL\s*([A-Z0-9\-]+)', re.IGNORECASE)
    
    found_bls = set()
    
    # Use the original pattern
    matches = bl_pattern.findall(text)
    found_bls.update(matches)
    
    # Use the BL-specific pattern
    bl_matches = bl_specific_pattern.findall(text)
    found_bls.update(bl_matches)
    
    # Filter out common bank reference patterns
    bank_ref_patterns = ['TEST', 'REF', 'BANK', 'PAY', 'TRANS', 'TXN']
    filtered_bls = set()
    
    for bl in found_bls:
        bl_upper = bl.upper()
        excluded = False
        for prefix in bank_ref_patterns:
            if bl_upper.startswith(prefix):
                excluded = True
                break
        if not excluded:
            filtered_bls.add(bl)
    
    return list(filtered_bls)

def fix_bl_numbers():
    """Fix BL numbers for emails that don't have them"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Get emails without BL numbers
        cursor.execute("""
            SELECT id, sender, subject, body, bl_numbers 
            FROM customer_emails 
            WHERE bl_numbers IS NULL OR array_length(bl_numbers, 1) IS NULL
            ORDER BY created_at DESC
            LIMIT 50
        """)
        
        emails = cursor.fetchall()
        print(f"Found {len(emails)} emails without BL numbers")
        
        fixed_count = 0
        for email_id, sender, subject, body, current_bl_numbers in emails:
            print(f"\n--- Email ID: {email_id} ---")
            print(f"Sender: {sender}")
            print(f"Subject: {subject}")
            print(f"Body: {body[:100]}...")
            print(f"Current BL numbers: {current_bl_numbers}")
            
            # Extract BL numbers from body
            extracted_bls = extract_bl_numbers_from_text(body)
            print(f"Extracted BL numbers: {extracted_bls}")
            
            if extracted_bls:
                # Update the email with extracted BL numbers
                cursor.execute(
                    "UPDATE customer_emails SET bl_numbers = %s WHERE id = %s",
                    (extracted_bls, email_id)
                )
                conn.commit()
                print(f"✅ Updated email {email_id} with BL numbers: {extracted_bls}")
                fixed_count += 1
            else:
                print(f"❌ No BL numbers found in email {email_id}")
        
        print(f"\n🎉 Fixed {fixed_count} emails with BL numbers")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_bl_numbers() 