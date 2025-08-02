#!/usr/bin/env python3
"""
Check for BL numbers in email subjects and bodies
"""

import os
import sys
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_db_conn

def check_bl_in_emails():
    """Check for BL numbers in email content"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Look for common BL number patterns in subjects and bodies
        cursor.execute("""
            SELECT id, sender, subject, body 
            FROM customer_emails 
            WHERE subject ILIKE '%BL%' 
               OR subject ILIKE '%bill%' 
               OR subject ILIKE '%lading%'
               OR body ILIKE '%BL%'
               OR body ILIKE '%bill%'
               OR body ILIKE '%lading%'
            LIMIT 10
        """)
        
        potential_bl_emails = cursor.fetchall()
        print(f"📧 Found {len(potential_bl_emails)} emails with potential BL references:")
        
        for email in potential_bl_emails:
            print(f"\nID: {email[0]}")
            print(f"Sender: {email[1]}")
            print(f"Subject: {email[2]}")
            
            # Extract potential BL numbers using regex
            content = f"{email[2]} {email[3] or ''}"
            
            # Look for common BL number patterns
            bl_patterns = [
                r'\bBL[-\s]?(\d{6,})\b',  # BL followed by 6+ digits
                r'\b(\d{6,})[-\s]?BL\b',  # 6+ digits followed by BL
                r'\bBill\s+of\s+Lading[:\s]*(\d{6,})\b',  # Bill of Lading followed by numbers
                r'\b(\d{6,})\s*[-.]?\s*NYC\b',  # Numbers followed by NYC
            ]
            
            found_bls = []
            for pattern in bl_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                found_bls.extend(matches)
            
            if found_bls:
                print(f"  🎯 Potential BL numbers found: {found_bls}")
            else:
                print(f"  ❌ No clear BL numbers found")
            
            # Show first 200 chars of body
            body_preview = (email[3] or '')[:200]
            if body_preview:
                print(f"  Body preview: {body_preview}...")
        
        # Also check for any emails with numbers that might be BL numbers
        cursor.execute("""
            SELECT id, sender, subject 
            FROM customer_emails 
            WHERE subject ~ '\d{6,}'
            LIMIT 5
        """)
        
        number_emails = cursor.fetchall()
        print(f"\n🔢 Found {len(number_emails)} emails with 6+ digit numbers in subject:")
        
        for email in number_emails:
            print(f"  ID: {email[0]}, Sender: {email[1]}")
            print(f"  Subject: {email[2]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_bl_in_emails() 