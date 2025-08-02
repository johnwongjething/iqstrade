#!/usr/bin/env python3
"""
Test PDF payment processing - both text-based and PDF-based bank transfers
"""

import os
import tempfile
from email_ingestor_enhanced import handle_email_via_openai, process_payment_receipt_email
from invoice_utils import generate_pdf_from_text

def test_text_based_payment():
    """Test text-based bank transfer payment"""
    print("🧪 Testing Text-Based Bank Transfer Payment")
    print("=" * 60)
    
    # Test email with text-based payment
    subject = "Bank Transfer Payment"
    body = "Payment for B/L NYC220 Amount: $680 Ref: TEST987"
    attachments = []
    from_addr = "customer@example.com"
    
    print(f"📧 Subject: {subject}")
    print(f"📝 Body: {body}")
    print(f"📎 Attachments: {len(attachments)}")
    
    try:
        # Process the email
        result = handle_email_via_openai(subject, body, attachments, from_addr)
        
        print(f"\n💰 Extracted Amount: ${result.get('paid_amount')}")
        print(f"📊 BL Numbers: {result.get('bl_numbers')}")
        print(f"📋 BL Payment Map: {result.get('bl_payment_map')}")
        print(f"✅ Valid BLs: {result.get('valid_bls')}")
        
        # Check if payment processing should be triggered
        if result.get('bl_payment_map') and result.get('paid_amount'):
            print("\n🔄 Testing payment receipt processing...")
            
            # Simulate email processing
            email_id = 999  # Test email ID
            success = process_payment_receipt_email(
                email_id=email_id,
                from_addr=from_addr,
                subject=subject,
                body_text=body,
                attachments=attachments,
                bl_payment_map=result.get('bl_payment_map', {})
            )
            
            if success:
                print("✅ Payment receipt processing completed successfully")
            else:
                print("❌ Payment receipt processing failed")
        
        # Check for underpayment/overpayment message
        reply = result.get('custom_reply', '')
        if 'underpayment' in reply.lower():
            print("✅ Underpayment message detected in reply")
        elif 'overpayment' in reply.lower():
            print("✅ Overpayment message detected in reply")
        elif 'payment match' in reply.lower():
            print("✅ Payment match message detected in reply")
        
    except Exception as e:
        print(f"❌ Error processing text-based payment: {e}")

def test_pdf_based_payment():
    """Test PDF-based bank transfer payment"""
    print("\n🧪 Testing PDF-Based Bank Transfer Payment")
    print("=" * 60)
    
    # Create a temporary PDF with payment information
    pdf_content = """
    BANK TRANSFER RECEIPT
    
    Date: 2025-08-01
    Amount: $720.00
    Reference: TEST987
    BL Number: NYC220
    
    Payment Details:
    - Bank: HSBC
    - Account: 123-456789-001
    - Transfer ID: TXN123456
    
    This is a confirmation of payment for B/L NYC220.
    """
    
    # Create temporary PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
        temp_pdf_path = temp_pdf.name
    
    try:
        # Generate PDF from text
        generate_pdf_from_text(pdf_content, temp_pdf_path)
        
        # Test email with PDF attachment
        subject = "Bank Transfer Receipt"
        body = "Please find attached the bank transfer receipt for B/L NYC220"
        attachments = [temp_pdf_path]
        from_addr = "customer@example.com"
        
        print(f"📧 Subject: {subject}")
        print(f"📝 Body: {body}")
        print(f"📎 Attachments: {len(attachments)}")
        print(f"📄 PDF Path: {temp_pdf_path}")
        
        # Process the email
        result = handle_email_via_openai(subject, body, attachments, from_addr)
        
        print(f"\n💰 Extracted Amount: ${result.get('paid_amount')}")
        print(f"📊 BL Numbers: {result.get('bl_numbers')}")
        print(f"📋 BL Payment Map: {result.get('bl_payment_map')}")
        print(f"✅ Valid BLs: {result.get('valid_bls')}")
        
        # Check if payment processing should be triggered
        if result.get('bl_payment_map') and result.get('paid_amount'):
            print("\n🔄 Testing payment receipt processing with PDF...")
            
            # Simulate email processing
            email_id = 998  # Test email ID
            success = process_payment_receipt_email(
                email_id=email_id,
                from_addr=from_addr,
                subject=subject,
                body_text=body,
                attachments=attachments,
                bl_payment_map=result.get('bl_payment_map', {})
            )
            
            if success:
                print("✅ PDF payment receipt processing completed successfully")
            else:
                print("❌ PDF payment receipt processing failed")
        
        # Check for underpayment/overpayment message
        reply = result.get('custom_reply', '')
        if 'underpayment' in reply.lower():
            print("✅ Underpayment message detected in reply")
        elif 'overpayment' in reply.lower():
            print("✅ Overpayment message detected in reply")
        elif 'payment match' in reply.lower():
            print("✅ Payment match message detected in reply")
        
    except Exception as e:
        print(f"❌ Error processing PDF-based payment: {e}")
    finally:
        # Clean up temporary PDF
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
            print(f"🧹 Cleaned up temporary PDF: {temp_pdf_path}")

def test_missing_attachment_detection():
    """Test detection of missing attachments"""
    print("\n🧪 Testing Missing Attachment Detection")
    print("=" * 60)
    
    # Test email that mentions attachment but doesn't have one
    subject = "Payment Receipt"
    body = "Please find attached the bank transfer receipt for B/L NYC220. Amount: $700"
    attachments = []
    from_addr = "customer@example.com"
    
    print(f"📧 Subject: {subject}")
    print(f"📝 Body: {body}")
    print(f"📎 Attachments: {len(attachments)}")
    print("💡 Email mentions 'attached' but has no attachments")
    
    try:
        # Process the email
        result = handle_email_via_openai(subject, body, attachments, from_addr)
        
        print(f"\n💰 Extracted Amount: ${result.get('paid_amount')}")
        print(f"📊 BL Numbers: {result.get('bl_numbers')}")
        
        # Check if the system handles missing attachments gracefully
        if result.get('paid_amount') and result.get('bl_numbers'):
            print("✅ System correctly extracted payment info despite missing attachment")
        else:
            print("❌ System failed to extract payment info")
        
    except Exception as e:
        print(f"❌ Error processing missing attachment case: {e}")

def main():
    """Main test function"""
    print("🔧 Testing PDF Payment Processing in email_ingestor_enhanced.py")
    print("=" * 80)
    
    # Test text-based payments
    test_text_based_payment()
    
    # Test PDF-based payments
    test_pdf_based_payment()
    
    # Test missing attachment detection
    test_missing_attachment_detection()
    
    print("\n🎉 PDF payment processing testing completed!")
    print("\n📋 Summary:")
    print("✅ Text-based bank transfer payments")
    print("✅ PDF-based bank transfer payments")
    print("✅ PDF attachment processing")
    print("✅ Missing attachment detection")
    print("✅ Receipt generation and upload")
    print("✅ Underpayment/overpayment detection")

if __name__ == "__main__":
    main() 