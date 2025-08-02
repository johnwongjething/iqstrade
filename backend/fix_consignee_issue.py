#!/usr/bin/env python3
"""
Fix consignee data in database - restore original consignee values
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_db_conn

def fix_consignee_data():
    """Fix consignee data by restoring from OCR text"""
    print("🔧 Fixing Consignee Data")
    print("=" * 40)
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Failed to connect to database")
            return
            
        cur = conn.cursor()
        
        # Find bills with empty consignee but have OCR text
        cur.execute("""
            SELECT id, bl_number, consignee, ocr_text 
            FROM bill_of_lading 
            WHERE (consignee IS NULL OR consignee = '' OR consignee = 'None')
            AND ocr_text IS NOT NULL
            ORDER BY id DESC
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            print("✅ No bills with empty consignee found")
            return
            
        print(f"🔍 Found {len(rows)} bills with empty consignee:")
        
        for row in rows:
            bill_id, bl_number, current_consignee, ocr_text = row
            print(f"   Bill ID {bill_id} (BL: {bl_number}): Current='{current_consignee}'")
            
            # Try to extract consignee from OCR text
            import json
            try:
                ocr_data = json.loads(ocr_text)
                original_consignee = ocr_data.get('consignee', '')
                
                if original_consignee and original_consignee != current_consignee:
                    # Update with original consignee
                    cur.execute("""
                        UPDATE bill_of_lading 
                        SET consignee = %s 
                        WHERE id = %s
                    """, (original_consignee, bill_id))
                    print(f"   ✅ Fixed: '{original_consignee}'")
                else:
                    print(f"   ⚠️  No original consignee found in OCR")
                    
            except Exception as e:
                print(f"   ❌ Error parsing OCR: {e}")
        
        conn.commit()
        print(f"\n✅ Processed {len(rows)} records")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_consignee_data() 