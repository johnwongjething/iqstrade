#!/usr/bin/env python3
"""
Script to fix existing database records with missing consignee information
This script will:
1. Find records with empty consignee fields
2. Re-process the OCR data to extract consignee from "CONSIGNED TO" format
3. Update the database with the corrected information
"""

import sys
import os
import json
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

from config import get_db_conn
from enhanced_ocr_processor import extract_fields_enhanced

def extract_consignee_from_text(text):
    """Extract consignee from text using regex patterns"""
    if not text:
        return None
    
    # Look for "CONSIGNED TO" patterns
    consignee_patterns = [
        r'CONSIGNED\s+TO[:\s]*\n*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)',
        r'CONSIGNED\s+TO[:\s]*\n*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)\s*\n',
        r'3\.\s*CONSIGNED\s+TO[:\s]*\n*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)',
        r'CONSIGNEE[:\s]*\n*([A-Z\s&\.]+(?:LTD|INC|LLC|CORP|CO|COMPANY)?)',
    ]
    
    for pattern in consignee_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        if matches:
            consignee = matches[0].strip()
            # Clean up the consignee name
            consignee = re.sub(r'\s+', ' ', consignee)  # Normalize whitespace
            consignee = consignee.strip()
            if len(consignee) > 3:  # Valid consignee name
                return consignee
    
    return None

def fix_existing_consignee_data():
    """Fix existing database records with missing consignee"""
    
    print("🔧 Fixing existing consignee data...")
    print("=" * 50)
    
    conn = get_db_conn()
    if not conn:
        print("❌ Database connection failed")
        return
    
    cursor = conn.cursor()
    
    try:
        # Find records with empty consignee
        cursor.execute("""
            SELECT id, ocr_text, consignee, shipper, bl_number 
            FROM bill_of_lading 
            WHERE (consignee IS NULL OR consignee = '' OR consignee = 'N/A')
            AND ocr_text IS NOT NULL
            ORDER BY id DESC
        """)
        
        records = cursor.fetchall()
        print(f"📊 Found {len(records)} records with missing consignee")
        
        fixed_count = 0
        for record in records:
            bill_id, ocr_text, current_consignee, shipper, bl_number = record
            
            print(f"\n🔍 Processing Bill ID {bill_id} (BL: {bl_number})")
            print(f"   Current consignee: '{current_consignee}'")
            
            try:
                # Parse OCR text
                if ocr_text:
                    ocr_data = json.loads(ocr_text)
                    raw_text = ocr_data.get('raw_text', '')
                    
                    if raw_text:
                        # Try to extract consignee from raw text
                        extracted_consignee = extract_consignee_from_text(raw_text)
                        
                        if extracted_consignee:
                            print(f"   ✅ Extracted consignee: '{extracted_consignee}'")
                            
                            # Update the database
                            cursor.execute("""
                                UPDATE bill_of_lading 
                                SET consignee = %s 
                                WHERE id = %s
                            """, (extracted_consignee, bill_id))
                            
                            fixed_count += 1
                            print(f"   ✅ Updated database")
                        else:
                            print(f"   ❌ Could not extract consignee from text")
                    else:
                        print(f"   ❌ No raw text found in OCR data")
                else:
                    print(f"   ❌ No OCR text found")
                    
            except Exception as e:
                print(f"   ❌ Error processing record: {e}")
                continue
        
        # Commit changes
        conn.commit()
        print(f"\n✅ Fixed {fixed_count} out of {len(records)} records")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def check_consignee_data():
    """Check the current state of consignee data"""
    
    print("🔍 Checking consignee data status...")
    print("=" * 40)
    
    conn = get_db_conn()
    if not conn:
        print("❌ Database connection failed")
        return
    
    cursor = conn.cursor()
    
    try:
        # Count records with missing consignee
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN consignee IS NULL OR consignee = '' OR consignee = 'N/A' THEN 1 END) as missing_consignee,
                COUNT(CASE WHEN consignee IS NOT NULL AND consignee != '' AND consignee != 'N/A' THEN 1 END) as has_consignee
            FROM bill_of_lading
        """)
        
        stats = cursor.fetchone()
        total, missing, has_consignee = stats
        
        print(f"📊 Consignee Data Status:")
        print(f"   Total records: {total}")
        print(f"   Records with consignee: {has_consignee}")
        print(f"   Records missing consignee: {missing}")
        print(f"   Completion rate: {(has_consignee/total*100):.1f}%" if total > 0 else "N/A")
        
        # Show some examples of missing consignee records
        if missing > 0:
            cursor.execute("""
                SELECT id, bl_number, shipper, consignee 
                FROM bill_of_lading 
                WHERE consignee IS NULL OR consignee = '' OR consignee = 'N/A'
                ORDER BY id DESC
                LIMIT 5
            """)
            
            examples = cursor.fetchall()
            print(f"\n📋 Examples of records with missing consignee:")
            for example in examples:
                bill_id, bl_number, shipper, consignee = example
                print(f"   ID {bill_id}: BL={bl_number}, Shipper='{shipper}', Consignee='{consignee}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("🔧 Consignee Data Fix Tool")
    print("=" * 30)
    
    # Check current status
    check_consignee_data()
    
    # Ask user if they want to proceed with fixes
    response = input("\nDo you want to proceed with fixing missing consignee data? (y/N): ")
    if response.lower() in ['y', 'yes']:
        fix_existing_consignee_data()
        print("\n✅ Fix process completed!")
    else:
        print("❌ Fix process cancelled.") 