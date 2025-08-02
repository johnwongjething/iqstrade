#!/usr/bin/env python3
"""
Check OCR data for bills with missing consignee
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_db_conn

def check_ocr_data():
    """Check OCR data for bills with missing consignee"""
    print("🔍 Checking OCR Data")
    print("=" * 40)
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Failed to connect to database")
            return
            
        cur = conn.cursor()
        
        # Check a specific bill
        cur.execute("""
            SELECT id, bl_number, consignee, ocr_text 
            FROM bill_of_lading 
            WHERE id = 197
        """)
        
        row = cur.fetchone()
        if row:
            bill_id, bl_number, current_consignee, ocr_text = row
            print(f"Bill {bill_id}: BL={bl_number}, Consignee='{current_consignee}'")
            
            try:
                ocr_data = json.loads(ocr_text)
                print("OCR fields:", list(ocr_data.keys()))
                print("OCR consignee:", ocr_data.get('consignee', 'NOT_FOUND'))
                print("OCR shipper:", ocr_data.get('shipper', 'NOT_FOUND'))
                print("OCR container_numbers:", ocr_data.get('container_numbers', 'NOT_FOUND'))
                print("OCR flight_or_vessel:", ocr_data.get('flight_or_vessel', 'NOT_FOUND'))
                
            except Exception as e:
                print(f"Error parsing OCR: {e}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_ocr_data() 