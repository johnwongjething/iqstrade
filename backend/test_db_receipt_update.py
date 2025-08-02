#!/usr/bin/env python3
"""
Test database receipt update functionality for both text-based and PDF-based receipts
"""

import os
import tempfile
from email_ingestor_enhanced import process_payment_receipt_email
from db_utils import get_db_conn
from cloudinary_utils import upload_filepath_to_cloudinary

def create_test_pdf(content, filename):
    """Create a test PDF file with proper formatting"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        c = canvas.Canvas(temp_path, pagesize=letter)
        
        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, "PAYMENT RECEIPT")
        
        # Add content lines
        c.setFont("Helvetica", 12)
        y_position = 720
        
        # Split content into lines and add them to PDF
        lines = content.strip().split('\n')
        for line in lines:
            if line.strip():  # Skip empty lines
                c.drawString(100, y_position, line.strip())
                y_position -= 20
        
        c.save()
        return temp_path
    except ImportError:
        print("ReportLab not available, creating text file instead")
        temp_path = os.path.join(tempfile.gettempdir(), filename.replace('.pdf', '.txt'))
        with open(temp_path, 'w') as f:
            f.write(content)
        return temp_path

def check_database_columns():
    """Check which fee columns exist in the database"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    print("🔍 Checking Database Schema")
    print("=" * 60)
    
    # Check what columns exist
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'bill_of_lading' 
        AND column_name LIKE '%fee%'
        ORDER BY column_name
    """)
    
    fee_columns = [row[0] for row in cursor.fetchall()]
    print(f"Fee columns found: {fee_columns}")
    
    # Check if calculated columns exist
    has_calculated = 'calculated_ctn_fee' in fee_columns and 'calculated_service_fee' in fee_columns
    has_original = 'ctn_fee' in fee_columns and 'service_fee' in fee_columns
    
    print(f"Has original fee columns: {has_original}")
    print(f"Has calculated fee columns: {has_calculated}")
    
    cursor.close()
    conn.close()
    
    return has_original, has_calculated

def test_receipt_db_update():
    """Test if receipt URLs are being updated in the database"""
    print("\n🧪 Testing Database Receipt Update")
    print("=" * 60)
    
    # Check database schema first
    has_original, has_calculated = check_database_columns()
    
    # Test data - using valid BL numbers
    test_cases = [
        {
            "name": "Text-based receipt - NYC220 (valid)",
            "email_id": 1001,
            "from_addr": "test@example.com",
            "subject": "Test Payment Receipt - Text",
            "body_text": "Payment for B/L NYC220 Amount: $700",
            "attachments": [],
            "bl_payment_map": {'NYC220': 700.0},
            "expected_success": True
        },
        {
            "name": "PDF-based receipt - NYC221 (valid)",
            "email_id": 1002,
            "from_addr": "test@example.com", 
            "subject": "Test Payment Receipt - PDF",
            "body_text": "Payment for B/L NYC221 Amount: $675",
            "attachments": [create_test_pdf("NYC221 Payment Receipt", "test_receipt_nyc221.pdf")],
            "bl_payment_map": {'NYC221': 675.0},
            "expected_success": True
        },
        {
            "name": "Mixed receipt - NYC223 (valid)",
            "email_id": 1003,
            "from_addr": "test@example.com",
            "subject": "Test Payment Receipt - Mixed",
            "body_text": "Payment for B/L NYC223 Amount: $675",
            "attachments": [create_test_pdf("NYC223 Payment Receipt", "test_receipt_nyc223.pdf")],
            "bl_payment_map": {'NYC223': 675.0},
            "expected_success": True
        },
        {
            "name": "Invalid BL - NYC224 (should fail)",
            "email_id": 1004,
            "from_addr": "test@example.com",
            "subject": "Test Payment Receipt - Invalid BL",
            "body_text": "Payment for B/L NYC224 Amount: $500",
            "attachments": [],
            "bl_payment_map": {'NYC224': 500.0},
            "expected_success": False
        },
        {
            "name": "Invalid BL - NYC225 (should fail)",
            "email_id": 1005,
            "from_addr": "test@example.com",
            "subject": "Test Payment Receipt - Invalid BL 2",
            "body_text": "Payment for B/L NYC225 Amount: $600",
            "attachments": [create_test_pdf("NYC225 Payment Receipt", "test_receipt_nyc225.pdf")],
            "bl_payment_map": {'NYC225': 600.0},
            "expected_success": False
        }
    ]
    
    # Check current database state
    conn = get_db_conn()
    cursor = conn.cursor()
    
    print("\n📋 Current Database State:")
    for bl in ['NYC220', 'NYC221', 'NYC223']:
        if has_calculated:
            cursor.execute("""
                SELECT bl_number, calculated_ctn_fee, calculated_service_fee, 
                       status, receipt_filename, receipt_uploaded_at 
                FROM bill_of_lading WHERE bl_number = %s
            """, (bl,))
        else:
            cursor.execute("""
                SELECT bl_number, ctn_fee, service_fee, 
                       status, receipt_filename, receipt_uploaded_at 
                FROM bill_of_lading WHERE bl_number = %s
            """, (bl,))
        
        current_record = cursor.fetchone()
        if current_record:
            print(f"   BL: {current_record[0]}")
            if has_calculated:
                print(f"   Calculated CTN: {current_record[1]}, Service: {current_record[2]}")
            else:
                print(f"   Original CTN: {current_record[1]}, Service: {current_record[2]}")
            print(f"   Status: {current_record[3]}")
            print(f"   Current Receipt: {current_record[4]}")
            print(f"   Current Timestamp: {current_record[5]}")
        else:
            print(f"   ❌ BL {bl} not found in database")
    
    # Process each test case
    for test_case in test_cases:
        print(f"\n🔄 Testing: {test_case['name']}")
        print(f"   Email ID: {test_case['email_id']}")
        print(f"   BL Payment Map: {test_case['bl_payment_map']}")
        print(f"   Has PDF: {len(test_case['attachments']) > 0}")
        
        # Process payment receipt
        success = process_payment_receipt_email(
            email_id=test_case['email_id'],
            from_addr=test_case['from_addr'],
            subject=test_case['subject'],
            body_text=test_case['body_text'],
            attachments=test_case['attachments'],
            bl_payment_map=test_case['bl_payment_map']
        )
        
        if success == test_case['expected_success']:
            print(f"   ✅ Result: {'SUCCESS' if success else 'FAILED'} (as expected)")
        else:
            print(f"   ❌ Result: {'SUCCESS' if success else 'FAILED'} (unexpected)")
    
    # Check updated database state
    print(f"\n📋 Updated Database State:")
    for bl in ['NYC220', 'NYC221', 'NYC223']:
        if has_calculated:
            cursor.execute("""
                SELECT bl_number, calculated_ctn_fee, calculated_service_fee, 
                       status, receipt_filename, receipt_uploaded_at 
                FROM bill_of_lading WHERE bl_number = %s
            """, (bl,))
        else:
            cursor.execute("""
                SELECT bl_number, ctn_fee, service_fee, 
                       status, receipt_filename, receipt_uploaded_at 
                FROM bill_of_lading WHERE bl_number = %s
            """, (bl,))
        
        updated_record = cursor.fetchone()
        if updated_record:
            print(f"   BL: {updated_record[0]}")
            if has_calculated:
                print(f"   Calculated CTN: {updated_record[1]}, Service: {updated_record[2]}")
            else:
                print(f"   Original CTN: {updated_record[1]}, Service: {updated_record[2]}")
            print(f"   Status: {updated_record[3]}")
            print(f"   New Receipt: {updated_record[4]}")
            print(f"   New Timestamp: {updated_record[5]}")
            
            # Check if receipt was updated
            if updated_record[4] and updated_record[4] != 'None':
                print(f"   ✅ Receipt URL was updated successfully!")
            else:
                print(f"   ❌ Receipt URL was NOT updated")
        else:
            print(f"   ❌ BL {bl} not found in database after update")
    
    cursor.close()
    conn.close()

def check_receipt_upload_logic():
    """Check the receipt upload logic in process_payment_receipt_email"""
    print(f"\n🔍 Analyzing Receipt Upload Logic")
    print("=" * 60)
    
    # Test different scenarios
    test_cases = [
        {
            "name": "Exact Payment ($700 for $700 invoice)",
            "bl_payment_map": {"NYC220": 700.0},
            "expected": "Should update DB"
        },
        {
            "name": "Overpayment ($720 for $700 invoice)", 
            "bl_payment_map": {"NYC220": 720.0},
            "expected": "Should update DB"
        },
        {
            "name": "Underpayment ($680 for $700 invoice)",
            "bl_payment_map": {"NYC220": 680.0},
            "expected": "Should NOT update DB (underpayment)"
        },
        {
            "name": "Split Payment ($350 each for $700 invoice)",
            "bl_payment_map": {"NYC220": 350.0, "OTHER": 350.0},
            "expected": "Should NOT update DB (underpayment per BL)"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 {test_case['name']}")
        print(f"   Payment Map: {test_case['bl_payment_map']}")
        print(f"   Expected: {test_case['expected']}")
        
        # Check if this would trigger DB update
        total_paid = sum(test_case['bl_payment_map'].values())
        invoice_amount = 700.0  # NYC220 total
        tolerance = 2.0
        
        for bl, paid_amount in test_case['bl_payment_map'].items():
            if bl == 'NYC220':
                if paid_amount < invoice_amount - tolerance:
                    print(f"   ❌ Would NOT update DB: Underpayment (${paid_amount} < ${invoice_amount - tolerance})")
                else:
                    print(f"   ✅ Would update DB: Payment sufficient (${paid_amount} >= ${invoice_amount - tolerance})")

def main():
    """Main test function"""
    print("🔧 Testing Database Receipt Update in email_ingestor_enhanced.py")
    print("=" * 80)
    
    # Test the logic first
    check_receipt_upload_logic()
    
    # Test actual database update
    test_receipt_db_update()
    
    print(f"\n🎯 Analysis Complete!")
    print(f"💡 If receipt URLs aren't updating, check:")
    print(f"   1. Payment amount vs invoice amount (underpayment check)")
    print(f"   2. BL number exists in database")
    print(f"   3. Database connection and permissions")
    print(f"   4. Correct fee columns are being used (ctn_fee vs calculated_ctn_fee)")

if __name__ == "__main__":
    main() 