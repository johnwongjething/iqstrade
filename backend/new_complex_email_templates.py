#!/usr/bin/env python3
"""
New Complex Email Templates for IQSTrade
Uses actual BL numbers from current database
"""

import json
import os
from generate_dummy_cloudinary_links import get_current_bl_numbers

def load_dummy_links():
    """Load dummy Cloudinary links"""
    try:
        with open('dummy_cloudinary_links.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ dummy_cloudinary_links.json not found. Run generate_dummy_cloudinary_links.py first.")
        return {}

def create_new_complex_email_templates():
    """Create new complex email templates using current database BL numbers"""
    
    # Get current BL numbers
    bl_numbers = get_current_bl_numbers()
    if not bl_numbers:
        print("❌ No BL numbers found in database")
        return {}
    
    # Load dummy links
    dummy_links = load_dummy_links()
    
    # Create templates using actual BL numbers
    templates = {
        1: {
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
            "expected_issues": "Should detect full payments for all three BLs"
        },
        
        2: {
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
            "expected_issues": "Should provide CTN numbers and confirm $400 payment"
        },
        
        3: {
            "type": "Complex",
            "number": 3, 
            "subject": "Complex Test 3 - PDF with Multiple BLs (Real BLs)",
            "body": "Please process the attached payment receipt for multiple shipments.",
            "attachments": [f"dummy-receipt-{bl_numbers[6]}.pdf"] if dummy_links else [],
            "expected_issues": "Should extract BL numbers and payment info from PDF"
        },
        
        4: {
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
            "expected_issues": "Customer sent $300, total invoice cost is $600, outstanding is $300"
        },
        
        5: {
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
            "expected_issues": "Should handle Allinpay reserve settlement requests"
        },
        
        6: {
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
            "expected_issues": "Should provide business hours and payment methods"
        },
        
        7: {
            "type": "Complex",
            "number": 7,
            "subject": "Complex Test 7 - CTN Processing Time (Real BLs)",
            "body": f"""Dear Team,

How long does it take to process CTN for {bl_numbers[16]}, {bl_numbers[17]}, and {bl_numbers[18]}?

Also, what are the total fees for each shipment?

Best regards,
John Doe""",
            "attachments": [],
            "expected_issues": "Should provide CTN processing time and fee information"
        },
        
        8: {
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
            "expected_issues": "Should handle valid and invalid BL numbers"
        },
        
        9: {
            "type": "Complex",
            "number": 9,
            "subject": "Complex Test 9 - Empty Body with PDF (Real BLs)",
            "body": "",
            "attachments": [f"dummy-receipt-{bl_numbers[0]}.pdf"] if dummy_links else [],
            "expected_issues": "Should extract information from PDF attachment only"
        },
        
        10: {
            "type": "Complex",
            "number": 10,
            "subject": "Complex Test 10 - Multiple Payment Receipts (Real BLs)",
            "body": f"""Dear IQS Trade,

Please find attached payment receipts for the following shipments:

1. {bl_numbers[0]} - $200 payment
2. {bl_numbers[1]} - $200 payment
3. {bl_numbers[2]} - $200 payment

Total amount: $600

Please confirm receipt and update the payment status.

Best regards,
John Doe""",
            "attachments": [
                f"dummy-receipt-{bl_numbers[0]}.pdf",
                f"dummy-receipt-{bl_numbers[1]}.pdf", 
                f"dummy-receipt-{bl_numbers[2]}.pdf"
            ] if dummy_links else [],
            "expected_issues": "Should process multiple payment receipts"
        }
    }
    
    return templates

def save_templates_to_file(templates, filename='new_complex_email_templates.json'):
    """Save templates to JSON file"""
    with open(filename, 'w') as f:
        json.dump(templates, f, indent=2)
    
    print(f"✅ Saved templates to {filename}")

def print_templates_summary(templates):
    """Print summary of created templates"""
    print("\n" + "="*80)
    print("📧 NEW COMPLEX EMAIL TEMPLATES SUMMARY")
    print("="*80)
    
    for template_id, template in templates.items():
        print(f"\n📄 Template {template_id}: {template['subject']}")
        print(f"   Type: {template['type']}")
        print(f"   Attachments: {len(template.get('attachments', []))}")
        print(f"   Expected Issues: {template.get('expected_issues', 'N/A')}")
        print(f"   Body Preview: {template['body'][:100]}...")
    
    print(f"\n📊 Total Templates: {len(templates)}")
    print(f"📊 Templates with Attachments: {sum(1 for t in templates.values() if t.get('attachments'))}")

def main():
    """Main function"""
    print("🚀 Creating New Complex Email Templates")
    print("="*60)
    
    # Create templates
    templates = create_new_complex_email_templates()
    
    if not templates:
        print("❌ No templates created")
        return
    
    # Print summary
    print_templates_summary(templates)
    
    # Save to file
    save_templates_to_file(templates)
    
    print("\n🎉 New complex email templates created successfully!")
    print("\n📋 Next Steps:")
    print("1. Review the templates in new_complex_email_templates.json")
    print("2. Test with email ingestion system")
    print("3. Verify classification and response quality")
    print("4. Update email sender scripts to use these templates")

if __name__ == "__main__":
    main() 