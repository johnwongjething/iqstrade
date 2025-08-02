#!/usr/bin/env python3
"""
Test payment processing with the exact scenario from the user's screenshot
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from email_ingestor_enhanced import handle_email_via_openai, process_payment_receipt_email
from db_utils import get_db_conn

def test_payment_processing():
    """Test with the exact email from the user's screenshot"""
    
    # Email details from the screenshot
    subject = "hgf"
    body = "Payment for B/L NYC220 Amount: $700 Ref: TEST987"
    from_addr = "Jething John <johnwongjething@gmail.com>"
    attachments = []
    
    print("🧪 Testing payment processing with exact email from screenshot...")
    print(f"Subject: {subject}")
    print(f"From: {from_addr}")
    print(f"Body: {body}")
    print("-" * 50)
    
    try:
        # Test AI processing
        result = handle_email_via_openai(subject, body, attachments, from_addr)
        
        print("✅ AI function completed successfully!")
        print(f"Classification: {result.get('classification')}")
        print(f"Confidence Score: {result.get('confidence_score')}")
        print(f"Request Types: {result.get('request_types', [])}")
        print(f"BL Numbers: {result.get('bl_numbers', [])}")
        print(f"Paid Amount: {result.get('paid_amount')}")
        print(f"BL Payment Map: {result.get('bl_payment_map', {})}")
        print(f"Valid BLs: {result.get('valid_bls', {})}")
        
        # Check if this should trigger payment processing
        request_types = result.get('request_types', [])
        bl_payment_map = result.get('bl_payment_map', {})
        
        request_types_lower = [r.lower() for r in request_types]
        is_payment_related = any(r in request_types_lower for r in ["payment_receipt", "payment_status", "combined_request"])
        is_actual_payment = is_payment_related and bl_payment_map
        
        print(f"\n📊 Payment Processing Check:")
        print(f"  Is payment related: {is_payment_related}")
        print(f"  Has payment data: {bool(bl_payment_map)}")
        print(f"  Is actual payment: {is_actual_payment}")
        
        if is_actual_payment:
            print("✅ Should trigger payment processing")
            
            # Test payment processing
            print("\n💾 Testing payment receipt processing...")
            
            # First, create a test email in the database
            conn = get_db_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO customer_emails (sender, subject, body, created_at, openai_processed, classification)
                VALUES (%s, %s, %s, NOW(), TRUE, %s)
                RETURNING id
            """, (from_addr, subject, body, result.get('classification')))
            
            email_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Test email created with ID: {email_id}")
            
            # Now test payment processing
            success = process_payment_receipt_email(
                email_id=email_id,
                from_addr=from_addr,
                subject=subject,
                body_text=body,
                attachments=attachments,
                bl_payment_map=bl_payment_map
            )
            
            if success:
                print("✅ Payment processing completed successfully!")
                
                # Verify the database was updated
                conn = get_db_conn()
                cursor = conn.cursor()
                
                # Check if email was marked as processed
                cursor.execute("""
                    SELECT processed_for_payments FROM customer_emails WHERE id = %s
                """, (email_id,))
                
                email_processed = cursor.fetchone()
                if email_processed and email_processed[0]:
                    print("✅ Email marked as processed_for_payments = TRUE")
                else:
                    print("❌ Email not marked as processed_for_payments")
                
                # Check if BL status was updated
                for bl_number in bl_payment_map.keys():
                    cursor.execute("""
                        SELECT id, bl_number, status, receipt_filename, receipt_uploaded_at
                        FROM bill_of_lading WHERE bl_number = %s
                    """, (bl_number,))
                    
                    bl_data = cursor.fetchone()
                    if bl_data:
                        bl_id, bl_num, status, receipt_filename, receipt_uploaded_at = bl_data
                        print(f"✅ BL {bl_num} (ID: {bl_id}):")
                        print(f"  Status: {status}")
                        print(f"  Receipt Filename: {receipt_filename}")
                        print(f"  Receipt Uploaded At: {receipt_uploaded_at}")
                        
                        if status == 'Awaiting Bank In' and receipt_filename:
                            print("✅ Payment processing successful - status updated and receipt uploaded!")
                        else:
                            print("❌ Payment processing incomplete - status or receipt missing")
                    else:
                        print(f"❌ BL {bl_number} not found in database")
                
                cursor.close()
                conn.close()
            else:
                print("❌ Payment processing failed")
        else:
            print("❌ Should NOT trigger payment processing")
            
    except Exception as e:
        print(f"❌ Error testing payment processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payment_processing() 