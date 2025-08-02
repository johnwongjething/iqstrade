#!/usr/bin/env python3
"""
Test upload validation logic to identify 400 error causes
"""

def test_upload_validation():
    """Test the validation logic from the upload route"""
    
    print("🔍 Testing Upload Validation Logic")
    print("=" * 50)
    
    # Test cases - simulate different request scenarios
    test_cases = [
        {
            "name": "Test Case 1: All fields present",
            "data": {
                "name": "Test Customer",
                "email": "test@example.com", 
                "phone": "1234567890",
                "bill_pdf": ["file1.pdf"],
                "invoice_pdf": None,
                "packing_pdf": None
            },
            "expected": "PASS"
        },
        {
            "name": "Test Case 2: Missing name",
            "data": {
                "name": "",
                "email": "test@example.com",
                "phone": "1234567890", 
                "bill_pdf": ["file1.pdf"],
                "invoice_pdf": None,
                "packing_pdf": None
            },
            "expected": "FAIL - Name is required"
        },
        {
            "name": "Test Case 3: Missing email",
            "data": {
                "name": "Test Customer",
                "email": "",
                "phone": "1234567890",
                "bill_pdf": ["file1.pdf"], 
                "invoice_pdf": None,
                "packing_pdf": None
            },
            "expected": "FAIL - Email is required"
        },
        {
            "name": "Test Case 4: Missing phone",
            "data": {
                "name": "Test Customer",
                "email": "test@example.com",
                "phone": "",
                "bill_pdf": ["file1.pdf"],
                "invoice_pdf": None, 
                "packing_pdf": None
            },
            "expected": "FAIL - Phone is required"
        },
        {
            "name": "Test Case 5: No files at all",
            "data": {
                "name": "Test Customer",
                "email": "test@example.com",
                "phone": "1234567890",
                "bill_pdf": [],
                "invoice_pdf": None,
                "packing_pdf": None
            },
            "expected": "FAIL - At least one PDF file is required"
        },
        {
            "name": "Test Case 6: Only invoice PDF",
            "data": {
                "name": "Test Customer", 
                "email": "test@example.com",
                "phone": "1234567890",
                "bill_pdf": [],
                "invoice_pdf": "invoice.pdf",
                "packing_pdf": None
            },
            "expected": "PASS"
        },
        {
            "name": "Test Case 7: Only packing PDF",
            "data": {
                "name": "Test Customer",
                "email": "test@example.com", 
                "phone": "1234567890",
                "bill_pdf": [],
                "invoice_pdf": None,
                "packing_pdf": "packing.pdf"
            },
            "expected": "PASS"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 {test_case['name']}")
        print(f"   Data: {test_case['data']}")
        
        # Simulate validation logic
        name = test_case['data']['name']
        email = test_case['data']['email'] 
        phone = test_case['data']['phone']
        bill_pdfs = test_case['data']['bill_pdf']
        invoice_pdf = test_case['data']['invoice_pdf']
        packing_pdf = test_case['data']['packing_pdf']
        
        # Validation checks (same as in upload route)
        errors = []
        
        if not name:
            errors.append("Name is required")
        if not email:
            errors.append("Email is required") 
        if not phone:
            errors.append("Phone is required")
        if not bill_pdfs and not invoice_pdf and not packing_pdf:
            errors.append("At least one PDF file is required")
        
        if errors:
            print(f"   ❌ FAILED: {', '.join(errors)}")
            print(f"   Expected: {test_case['expected']}")
        else:
            print(f"   ✅ PASSED")
            print(f"   Expected: {test_case['expected']}")

def check_common_issues():
    """Check for common issues that might cause 400 errors"""
    
    print("\n🔍 Common Issues Check")
    print("=" * 30)
    
    issues = [
        "1. Missing required form fields (name, email, phone)",
        "2. No PDF files uploaded",
        "3. File size too large",
        "4. Invalid file format (not PDF)",
        "5. JWT token missing or expired",
        "6. CORS issues (if testing from frontend)",
        "7. Content-Type header incorrect",
        "8. Missing multipart/form-data encoding"
    ]
    
    for issue in issues:
        print(f"   • {issue}")
    
    print("\n💡 To debug:")
    print("   • Check browser developer tools Network tab")
    print("   • Look at the request payload and headers")
    print("   • Check server logs for specific error messages")

if __name__ == "__main__":
    test_upload_validation()
    check_common_issues() 