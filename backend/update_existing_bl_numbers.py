#!/usr/bin/env python3
"""
Update existing emails with BL numbers extracted from their content
"""

import os
import sys
import re
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_db_conn

def extract_bl_numbers(text):
    """Extract BL numbers from text using various patterns"""
    if not text:
        return []
    
    bl_patterns = [
        r'\bBL[-\s]?(\d{6,})\b',  # BL followed by 6+ digits
        r'\b(\d{6,})[-\s]?BL\b',  # 6+ digits followed by BL
        r'\bBill\s+of\s+Lading[:\s]*(\d{6,})\b',  # Bill of Lading followed by numbers
        r'\b(\d{6,})\s*[-.]?\s*NYC\b',  # Numbers followed by NYC
        r'\bNYC(\d{3,})\b',  # NYC followed by 3+ digits
        r'\b(\d{3,})[-.]?\s*NYC\b',  # 3+ digits followed by NYC
        r'\bBL\s*(\d{3,}[-.]?\d{3,})\b',  # BL with format like 001-123
    ]
    
    found_bls = set()
    for pattern in bl_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Clean up the match
            bl = match.strip()
            if bl and len(bl) >= 3:  # Minimum length for BL number
                found_bls.add(bl)
    
    return list(found_bls)

def update_existing_bl_numbers():
    """Update existing emails with extracted BL numbers"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Get all emails that don't have BL numbers
        cursor.execute("""
            SELECT id, sender, subject, body, bl_numbers 
            FROM customer_emails 
            WHERE bl_numbers IS NULL OR array_length(bl_numbers, 1) IS NULL
            ORDER BY created_at DESC
        """)
        
        emails = cursor.fetchall()
        print(f"📧 Found {len(emails)} emails without BL numbers")
        
        updated_count = 0
        
        for email in emails:
            email_id, sender, subject, body, existing_bls = email
            
            # Combine subject and body for extraction
            content = f"{subject or ''} {body or ''}"
            
            # Extract BL numbers
            bl_numbers = extract_bl_numbers(content)
            
            if bl_numbers:
                # Update the email with extracted BL numbers
                cursor.execute(
                    "UPDATE customer_emails SET bl_numbers = %s WHERE id = %s",
                    (bl_numbers, email_id)
                )
                updated_count += 1
                print(f"✅ Updated email {email_id}: {bl_numbers}")
            else:
                # Set empty array if no BL numbers found
                cursor.execute(
                    "UPDATE customer_emails SET bl_numbers = %s WHERE id = %s",
                    ([], email_id)
                )
                print(f"⏭️ Email {email_id}: No BL numbers found")
        
        conn.commit()
        print(f"\n🎉 Successfully updated {updated_count} emails with BL numbers")
        
        # Verify the update
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_emails 
            WHERE bl_numbers IS NOT NULL AND array_length(bl_numbers, 1) > 0
        """)
        
        emails_with_bl = cursor.fetchone()[0]
        print(f"📊 Total emails with BL numbers: {emails_with_bl}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_existing_bl_numbers() 