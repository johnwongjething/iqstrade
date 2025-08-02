#!/usr/bin/env python3
"""
New Complex Email Templates V2 - Using Current Database BL Numbers
Simplified version for better performance
"""

def create_new_complex_emails():
    """Create new complex email templates using current database BL numbers"""
    
    # These are the BL numbers from your current database (BL-2024-001 to BL-2024-020)
    bl_numbers = [
        "BL-2024-001", "BL-2024-002", "BL-2024-003", "BL-2024-004", "BL-2024-005",
        "BL-2024-006", "BL-2024-007", "BL-2024-008", "BL-2024-009", "BL-2024-010", 
        "BL-2024-011", "BL-2024-012", "BL-2024-013", "BL-2024-014", "BL-2024-015",
        "BL-2024-016", "BL-2024-017", "BL-2024-018", "BL-2024-019", "BL-2024-020"
    ]
    
    # Create dummy Cloudinary links
    dummy_links = {}
    for bl in bl_numbers:
        dummy_links[bl] = {
            'invoice': f"http://dummy-invoice-{bl}.pdf",
            'receipt': f"http://dummy-receipt-{bl}.pdf",
            'ctn': f"http://dummy-ctn-{bl}.pdf"
        }
    
    # New complex email templates
    new_complex_emails = [
        {
            "type": "Complex",
            "number": 1,
            "subject": "Complex Test 1 - Mixed Payment Types (Real BLs)",
            "body": f"""Dear IQS Trade Team,

I need to make payments for multiple shipments:

1. {bl_numbers[0]}: USD 200 (full payment)
2. {bl_numbers[1]}: USD 200 (full payment) 
3. {bl_numbers[2]}: USD 200 (full payment)

Also, please provide CTN numbers for all three shipments and send invoices.

Best regards,
John Doe""",
            "attachments": [],
            "dummy_links": [dummy_links[bl_numbers[0]]['invoice'], dummy_links[bl_numbers[1]]['invoice'], dummy_links[bl_numbers[2]]['invoice']]
        },
        
        {
            "type": "Complex",
            "number": 2, 
            "subject": "Complex Test 2 - Chinese + English Mixed (Real BLs)",
            "body": f"""Hello IQS Trade,

请问{bl_numbers[3]}和{bl_numbers[4]}的CTN号码是多少？

Also, I have paid $400 for {bl_numbers[5]}. Please confirm receipt.

另外，请告知营业时间和付款方式。

Thanks,
John""",
            "attachments": [],
            "dummy_links": [dummy_links[bl_numbers[5]]['receipt']]
        },
        
        {
            "type": "Complex",
            "number": 3,
            "subject": "Complex Test 3 - PDF with Multiple BLs (Real BLs)", 
            "body": "Please process the attached payment receipt for multiple shipments.",
            "attachments": [f"dummy-receipt-{bl_numbers[6]}.pdf"],
            "dummy_links": [dummy_links[bl_numbers[6]]['receipt']]
        },
        
        {
            "type": "Complex",
            "number": 4,
            "subject": "Complex Test 4 - Underpayment Scenario (Real BLs)",
            "body": f"""Hi Team,

I'm sending payment for:
- {bl_numbers[7]}: $100 (should be $200 total)
- {bl_numbers[8]}: $150 (should be $200 total)
- {bl_numbers[9]}: $50 (should be $200 total)

Total sent: $300. Please confirm what's still due.

Thanks,
John""",
            "attachments": [],
            "dummy_links": [dummy_links[bl_numbers[7]]['receipt'], dummy_links[bl_numbers[8]]['receipt'], dummy_links[bl_numbers[9]]['receipt']]
        },
        
        {
            "type": "Complex",
            "number": 5,
            "subject": "Complex Test 5 - Allinpay Reserve Settlement (Real BLs)",
            "body": f"""Dear IQS Trade,

I need to settle the reserve for the following Allinpay shipments:

1. {bl_numbers[10]} (Reserve Settled)
2. {bl_numbers[11]} (Unsettled - need to settle 15%)
3. {bl_numbers[12]} (Unsettled - need to settle 15%)

Please provide the settlement instructions and confirm the amounts.

Best regards,
John Doe""",
            "attachments": [],
            "dummy_links": []
        },
        
        {
            "type": "Complex",
            "number": 6,
            "subject": "Complex Test 6 - Business Hours + Payment Methods (Real BLs)",
            "body": f"""Hi IQS Trade,

What are your business hours? Also, what payment methods do you accept?

I need to pay for {bl_numbers[13]} ($200), {bl_numbers[14]} ($200), and {bl_numbers[15]} ($200).

Please provide payment instructions.

Thanks,
John""",
            "attachments": [],
            "dummy_links": []
        },
        
        {
            "type": "Complex",
            "number": 7,
            "subject": "Complex Test 7 - CTN Processing Time (Real BLs)",
            "body": f"""Dear Team,

How long does it take to process CTN for {bl_numbers[16]}, {bl_numbers[17]}, and {bl_numbers[18]}?

Also, what are the total fees for each shipment?

Best regards,
John Doe""",
            "attachments": [],
            "dummy_links": []
        },
        
        {
            "type": "Complex",
            "number": 8,
            "subject": "Complex Test 8 - Invalid BL Mixed with Valid (Real BLs)",
            "body": f"""Hello,

I need information for:
- {bl_numbers[19]} (valid)
- BL-INVALID999 (invalid)
- BL-TEST123 (invalid)

Please provide CTN numbers and payment status for all shipments.

Regards,
John""",
            "attachments": [],
            "dummy_links": []
        }
    ]
    
    return new_complex_emails, dummy_links

def print_email_summary(emails, dummy_links):
    """Print summary of created emails"""
    print("\n" + "="*80)
    print("📧 NEW COMPLEX EMAIL TEMPLATES SUMMARY")
    print("="*80)
    
    for email in emails:
        print(f"\n📄 Template {email['number']}: {email['subject']}")
        print(f"   Type: {email['type']}")
        print(f"   Attachments: {len(email.get('attachments', []))}")
        print(f"   Dummy Links: {len(email.get('dummy_links', []))}")
        print(f"   Body Preview: {email['body'][:100]}...")
    
    print(f"\n📊 Total Templates: {len(emails)}")
    print(f"📊 Total BL Numbers Used: 20")
    print(f"📊 Total Dummy Links: {len(dummy_links) * 3}")

def main():
    """Main function"""
    print("🚀 Creating New Complex Email Templates V2")
    print("="*60)
    
    # Create emails and dummy links
    emails, dummy_links = create_new_complex_emails()
    
    # Print summary
    print_email_summary(emails, dummy_links)
    
    print("\n🎉 New complex email templates created successfully!")
    print("\n📋 Key Features:")
    print("✅ Uses real BL numbers from current database")
    print("✅ Includes dummy Cloudinary links")
    print("✅ Covers complex scenarios (payments, CTN, Allinpay)")
    print("✅ Mixed Chinese/English content")
    print("✅ Invalid BL number handling")
    
    print("\n📋 Next Steps:")
    print("1. Use these templates in your email testing")
    print("2. Test with email ingestion system")
    print("3. Verify classification and response quality")

if __name__ == "__main__":
    main() 