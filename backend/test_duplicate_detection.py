#!/usr/bin/env python3
"""
Simple test script to verify duplicate payment detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.balance_utils import check_payment_processed, mark_payment_processed
from config import get_db_conn

def test_duplicate_detection():
    """Test duplicate payment detection for a specific BL"""
    
    # Test BL number (replace with an actual BL number from your database)
    test_bl_number = "NYC226"  # Use the BL number from the user's report
    
    print(f"Testing duplicate payment detection for BL: {test_bl_number}")
    
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Get BL ID
        cur.execute("SELECT id FROM bill_of_lading WHERE bl_number = %s", (test_bl_number,))
        result = cur.fetchone()
        
        if not result:
            print(f"❌ BL {test_bl_number} not found in database")
            return
        
        bl_id = result[0]
        print(f"✅ Found BL {test_bl_number} with ID: {bl_id}")
        
        # Check if payment already processed
        is_processed = check_payment_processed(bl_id, 'email')
        print(f"🔍 Payment processed check: {is_processed}")
        
        if is_processed:
            print("✅ Duplicate payment detection is working correctly!")
            
            # Show existing transactions
            cur.execute("""
                SELECT id, username, transaction_type, amount, payment_source, description, created_at
                FROM customer_balance_transactions 
                WHERE reference_id = %s AND payment_source = 'email'
                ORDER BY created_at DESC
            """, (bl_id,))
            
            transactions = cur.fetchall()
            print(f"📋 Found {len(transactions)} existing transactions:")
            for txn in transactions:
                print(f"  - ID: {txn[0]}, User: {txn[1]}, Type: {txn[2]}, Amount: {txn[3]}, Source: {txn[4]}, Created: {txn[6]}")
        else:
            print("ℹ️ No previous payment found - this would be a new payment")
            
            # Test marking as processed
            print("🧪 Testing mark_payment_processed...")
            mark_payment_processed(bl_id, 'email', 'test_script')
            
            # Check again
            is_processed_after = check_payment_processed(bl_id, 'email')
            print(f"🔍 Payment processed check after marking: {is_processed_after}")
            
            if is_processed_after:
                print("✅ mark_payment_processed is working correctly!")
            else:
                print("❌ mark_payment_processed is not working correctly!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_duplicate_detection() 