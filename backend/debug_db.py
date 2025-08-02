#!/usr/bin/env python3
"""
Debug script to check container_numbers and flight_or_vessel in database
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_db_conn

def debug_database():
    """Check what's actually stored in the database"""
    print("🔍 Debugging Database Contents")
    print("=" * 50)
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Failed to connect to database")
            return
            
        cur = conn.cursor()
        
        # Check recent bills
        cur.execute("""
            SELECT id, bl_number, container_numbers, flight_or_vessel, 
                   shipment_type, container_count, total_weight_kg,
                   calculated_ctn_fee, calculated_service_fee
            FROM bill_of_lading 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            print("❌ No bills found in database")
            return
            
        print(f"📋 Found {len(rows)} recent bills:")
        print()
        
        for row in rows:
            (bill_id, bl_number, container_numbers, flight_or_vessel, 
             shipment_type, container_count, total_weight_kg,
             calculated_ctn_fee, calculated_service_fee) = row
            
            print(f"🔸 Bill ID: {bill_id}")
            print(f"   BL Number: {bl_number}")
            print(f"   Container Numbers: '{container_numbers}' (type: {type(container_numbers)})")
            print(f"   Flight/Vessel: '{flight_or_vessel}' (type: {type(flight_or_vessel)})")
            print(f"   Shipment Type: {shipment_type}")
            print(f"   Container Count: {container_count}")
            print(f"   Total Weight: {total_weight_kg} kg")
            print(f"   CTN Fee: ${calculated_ctn_fee}")
            print(f"   Service Fee: ${calculated_service_fee}")
            print()
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_database() 