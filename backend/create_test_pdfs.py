#!/usr/bin/env python3
"""
Create 3 PDF sample files for testing payment scenarios
"""

import os
from invoice_utils import generate_pdf_from_text

def create_test_pdfs():
    """Create 3 different PDF samples for testing"""
    
    # Create test directory if it doesn't exist
    test_dir = "test_pdfs"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        print(f"📁 Created test directory: {test_dir}")
    
    # Sample 1: Underpayment PDF
    underpayment_content = """
    BANK TRANSFER RECEIPT
    
    Date: 2025-08-01
    Time: 14:30:25
    Transaction ID: TXN123456789
    
    PAYMENT DETAILS:
    Amount: $680.00
    Currency: USD
    Reference: TEST987
    BL Number: NYC220
    
    BANK INFORMATION:
    Bank: HSBC Bank
    Account: 123-456789-001
    Account Holder: Customer Name
    
    TRANSFER DETAILS:
    From: Customer Bank Account
    To: IQSTrade Account
    Method: Online Banking Transfer
    
    This is a confirmation of payment for B/L NYC220.
    Note: This payment is for partial amount of the invoice.
    
    Thank you for your payment.
    """
    
    # Sample 2: Overpayment PDF
    overpayment_content = """
    BANK TRANSFER RECEIPT
    
    Date: 2025-08-01
    Time: 15:45:12
    Transaction ID: TXN987654321
    
    PAYMENT DETAILS:
    Amount: $720.00
    Currency: USD
    Reference: TEST456
    BL Number: NYC220
    
    BANK INFORMATION:
    Bank: Standard Chartered Bank
    Account: 987-654321-002
    Account Holder: Customer Name
    
    TRANSFER DETAILS:
    From: Customer Bank Account
    To: IQSTrade Account
    Method: Mobile Banking Transfer
    
    This is a confirmation of payment for B/L NYC220.
    Note: This payment exceeds the invoice amount.
    
    Thank you for your payment.
    """
    
    # Sample 3: Exact Payment PDF
    exact_payment_content = """
    BANK TRANSFER RECEIPT
    
    Date: 2025-08-01
    Time: 16:20:33
    Transaction ID: TXN555666777
    
    PAYMENT DETAILS:
    Amount: $700.00
    Currency: USD
    Reference: TEST789
    BL Number: NYC220
    
    BANK INFORMATION:
    Bank: Bank of China
    Account: 555-666777-003
    Account Holder: Customer Name
    
    TRANSFER DETAILS:
    From: Customer Bank Account
    To: IQSTrade Account
    Method: Internet Banking Transfer
    
    This is a confirmation of payment for B/L NYC220.
    Note: This payment matches the invoice amount exactly.
    
    Thank you for your payment.
    """
    
    # Generate the PDFs
    pdfs = [
        {
            "name": "underpayment_receipt.pdf",
            "content": underpayment_content,
            "description": "Underpayment ($680 for $700 invoice)"
        },
        {
            "name": "overpayment_receipt.pdf", 
            "content": overpayment_content,
            "description": "Overpayment ($720 for $700 invoice)"
        },
        {
            "name": "exact_payment_receipt.pdf",
            "content": exact_payment_content,
            "description": "Exact Payment ($700 for $700 invoice)"
        }
    ]
    
    created_files = []
    
    for pdf in pdfs:
        file_path = os.path.join(test_dir, pdf["name"])
        try:
            generate_pdf_from_text(pdf["content"], file_path)
            created_files.append(file_path)
            print(f"✅ Created: {pdf['name']} - {pdf['description']}")
        except Exception as e:
            print(f"❌ Failed to create {pdf['name']}: {e}")
    
    print(f"\n🎉 Successfully created {len(created_files)} PDF files in '{test_dir}' directory")
    print("\n📋 PDF Files Created:")
    for file_path in created_files:
        file_size = os.path.getsize(file_path)
        print(f"   📄 {os.path.basename(file_path)} ({file_size} bytes)")
    
    print(f"\n💡 Test these PDFs with:")
    print(f"   python test_pdf_payment_processing.py")
    print(f"   python test_payment_logic.py")
    
    return created_files

if __name__ == "__main__":
    create_test_pdfs() 