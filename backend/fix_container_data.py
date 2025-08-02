#!/usr/bin/env python3
"""
Fix malformed container numbers data in database
"""

import os
import sys
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_db_conn

def fix_container_data():
    """Fix malformed container numbers in database"""
    print("🔧 Fixing Container Data")
    print("=" * 40)
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Failed to connect to database")
            return
            
        cur = conn.cursor()
        
        # Find bills with malformed container numbers
        cur.execute("""
            SELECT id, container_numbers 
            FROM bill_of_lading 
            WHERE container_numbers LIKE '%[%' OR container_numbers LIKE '%]%'
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            print("✅ No malformed container data found")
            return
            
        print(f"🔍 Found {len(rows)} bills with malformed container data:")
        
        for row in rows:
            bill_id, container_numbers = row
            print(f"   Bill ID {bill_id}: '{container_numbers}'")
            
            # Fix the data
            if container_numbers and container_numbers != '[]':
                # Extract container numbers from string representation of list
                matches = re.findall(r"'([^']+)'", container_numbers)
                if matches:
                    fixed_data = ', '.join(matches)
                    cur.execute("""
                        UPDATE bill_of_lading 
                        SET container_numbers = %s 
                        WHERE id = %s
                    """, (fixed_data, bill_id))
                    print(f"   ✅ Fixed: '{fixed_data}'")
                else:
                    # Try to extract any alphanumeric container numbers
                    matches = re.findall(r'[A-Z]{4}\d{7}', container_numbers)
                    if matches:
                        fixed_data = ', '.join(matches)
                        cur.execute("""
                            UPDATE bill_of_lading 
                            SET container_numbers = %s 
                            WHERE id = %s
                        """, (fixed_data, bill_id))
                        print(f"   ✅ Fixed: '{fixed_data}'")
                    else:
                        print(f"   ❌ Could not extract container numbers")
            else:
                print(f"   ⚠️  Empty container data, skipping")
        
        conn.commit()
        print(f"\n✅ Fixed {len(rows)} records")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_container_data() 