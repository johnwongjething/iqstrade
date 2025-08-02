#!/usr/bin/env python3
"""
Check current BL records in database
"""

from db_utils import get_db_conn

def check_bl_records():
    """Check current BL records"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    print("Current BL records:")
    print("=" * 80)
    
    # First check what columns exist
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'bill_of_lading' 
        AND column_name LIKE '%fee%'
        ORDER BY column_name
    """)
    
    fee_columns = [row[0] for row in cursor.fetchall()]
    print(f"Fee columns in bill_of_lading: {fee_columns}")
    print()
    
    # Check BL records with both old and new fee columns
    cursor.execute("""
        SELECT bl_number, ctn_fee, service_fee, calculated_ctn_fee, calculated_service_fee, 
               status, receipt_filename, receipt_uploaded_at
        FROM bill_of_lading 
        WHERE bl_number IN ('NYC220', 'NYC221', 'NYC223')
        ORDER BY bl_number
    """)
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"BL: {row[0]}")
            print(f"  Original CTN Fee: {row[1]}")
            print(f"  Original Service Fee: {row[2]}")
            print(f"  Calculated CTN Fee: {row[3]}")
            print(f"  Calculated Service Fee: {row[4]}")
            print(f"  Status: {row[5]}")
            print(f"  Receipt Filename: {row[6]}")
            print(f"  Receipt Uploaded At: {row[7]}")
            print("-" * 40)
    else:
        print("No BL records found for NYC220, NYC221, NYC223")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_bl_records() 