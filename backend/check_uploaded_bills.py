#!/usr/bin/env python3
"""
Check uploaded bills in database
"""

import json
from db_utils import get_db_conn
from datetime import datetime, timedelta

def check_recent_bills():
    """Check bills uploaded in the last 24 hours"""
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Get bills from the last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    
    cur.execute("""
        SELECT id, customer_name, customer_email, created_at, 
               shipper, consignee, bl_number, container_numbers, 
               flight_or_vessel, status, pdf_filename
        FROM bill_of_lading 
        WHERE created_at > %s
        ORDER BY created_at DESC
    """, (yesterday,))
    
    bills = cur.fetchall()
    
    print(f"📊 Found {len(bills)} bills uploaded in the last 24 hours:")
    print("=" * 80)
    
    for bill in bills:
        (id, customer_name, customer_email, created_at, 
         shipper, consignee, bl_number, container_numbers, 
         flight_or_vessel, status, pdf_filename) = bill
        
        print(f"📄 Bill ID: {id}")
        print(f"   Customer: {customer_name} ({customer_email})")
        print(f"   Created: {created_at}")
        print(f"   Status: {status}")
        print(f"   PDF: {pdf_filename}")
        print(f"   Shipper: {shipper or 'N/A'}")
        print(f"   Consignee: {consignee or 'N/A'}")
        print(f"   BL Number: {bl_number or 'N/A'}")
        print(f"   Container Numbers: {container_numbers or 'N/A'}")
        print(f"   Flight/Vessel: {flight_or_vessel or 'N/A'}")
        
        # Check if OCR data is complete
        has_ocr_data = any([shipper, consignee, bl_number, container_numbers, flight_or_vessel])
        ocr_status = "✅ Complete" if has_ocr_data else "❌ Incomplete"
        print(f"   OCR Status: {ocr_status}")
        print("-" * 40)
    
    cur.close()
    conn.close()

def check_all_bills():
    """Check all bills in the database"""
    conn = get_db_conn()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN shipper != '' THEN 1 END) as with_shipper,
               COUNT(CASE WHEN consignee != '' THEN 1 END) as with_consignee,
               COUNT(CASE WHEN bl_number != '' THEN 1 END) as with_bl_number,
               COUNT(CASE WHEN container_numbers != '' THEN 1 END) as with_containers,
               COUNT(CASE WHEN flight_or_vessel != '' THEN 1 END) as with_vessel
        FROM bill_of_lading
    """)
    
    stats = cur.fetchone()
    
    print("📊 Database Statistics:")
    print("=" * 40)
    print(f"Total Bills: {stats[0]}")
    print(f"With Shipper: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
    print(f"With Consignee: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
    print(f"With BL Number: {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
    print(f"With Container Numbers: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
    print(f"With Flight/Vessel: {stats[5]} ({stats[5]/stats[0]*100:.1f}%)")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    print("🔍 Checking uploaded bills...")
    print()
    
    check_recent_bills()
    print()
    check_all_bills() 