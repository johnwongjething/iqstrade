#!/usr/bin/env python3
"""
Generate Dummy Cloudinary Links for Email Testing
Creates dummy URLs for all BL numbers in the current database
"""

import os
import sys
from config import get_db_conn

def get_current_bl_numbers():
    """Get all BL numbers from the current database"""
    conn = get_db_conn()
    if not conn:
        print("❌ Failed to connect to database")
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT bl_number FROM bill_of_lading ORDER BY id")
    bl_numbers = [row[0] for row in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return bl_numbers

def generate_dummy_cloudinary_links():
    """Generate dummy Cloudinary URLs for all BL numbers"""
    bl_numbers = get_current_bl_numbers()
    
    if not bl_numbers:
        print("❌ No BL numbers found in database")
        return {}
    
    print(f"📋 Found {len(bl_numbers)} BL numbers in database")
    
    dummy_links = {}
    for bl in bl_numbers:
        # Create different types of dummy links
        dummy_links[bl] = {
            'invoice': f"http://dummy-invoice-{bl}.pdf",
            'receipt': f"http://dummy-receipt-{bl}.pdf",
            'ctn': f"http://dummy-ctn-{bl}.pdf",
            'packing_list': f"http://dummy-packing-{bl}.pdf"
        }
    
    return dummy_links

def save_dummy_links_to_file(dummy_links, filename='dummy_cloudinary_links.json'):
    """Save dummy links to a JSON file"""
    import json
    
    with open(filename, 'w') as f:
        json.dump(dummy_links, f, indent=2)
    
    print(f"✅ Saved dummy links to {filename}")

def print_dummy_links_summary(dummy_links):
    """Print a summary of generated dummy links"""
    print("\n" + "="*60)
    print("📋 DUMMY CLOUDINARY LINKS SUMMARY")
    print("="*60)
    
    for bl, links in dummy_links.items():
        print(f"\n📄 {bl}:")
        for link_type, url in links.items():
            print(f"   {link_type}: {url}")
    
    print(f"\n📊 Total BL numbers: {len(dummy_links)}")
    print(f"📊 Total dummy links: {len(dummy_links) * 4}")

def main():
    """Main function"""
    print("🚀 Generating Dummy Cloudinary Links for Email Testing")
    print("="*60)
    
    # Generate dummy links
    dummy_links = generate_dummy_cloudinary_links()
    
    if not dummy_links:
        print("❌ No dummy links generated")
        return
    
    # Print summary
    print_dummy_links_summary(dummy_links)
    
    # Save to file
    save_dummy_links_to_file(dummy_links)
    
    print("\n🎉 Dummy Cloudinary links generated successfully!")
    print("\n📋 Next Steps:")
    print("1. Use these links in your email templates")
    print("2. Test email processing with dummy attachments")
    print("3. Verify OCR and classification work correctly")

if __name__ == "__main__":
    main() 