#!/usr/bin/env python3
"""
Analyze email ID sequence issues and duplicate detection
"""

from config import get_db_conn
from datetime import datetime, timedelta

def analyze_email_sequence():
    """Analyze the email ID sequence and duplicate detection issues"""
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔍 Analyzing Email ID Sequence Issues...")
        
        # 1. Check recent emails and their IDs
        print("\n1. Recent emails (last 24 hours) - ID sequence:")
        cursor.execute("""
            SELECT id, sender, subject, created_at, message_id
            FROM customer_emails 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        recent_emails = cursor.fetchall()
        if recent_emails:
            print("   ID    | Created At          | Subject")
            print("   ------|---------------------|------------------")
            for email in recent_emails:
                email_id, sender, subject, created_at, message_id = email
                print(f"   {email_id:6d} | {created_at.strftime('%H:%M:%S')} | {subject[:30]}...")
        
        # 2. Check for gaps in ID sequence
        print(f"\n2. ID sequence gaps analysis:")
        cursor.execute("""
            SELECT id, LAG(id) OVER (ORDER BY id) as prev_id
            FROM customer_emails 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY id
        """)
        
        id_sequence = cursor.fetchall()
        gaps = []
        for row in id_sequence:
            current_id, prev_id = row
            if prev_id and current_id - prev_id > 1:
                gaps.append((prev_id, current_id, current_id - prev_id - 1))
        
        if gaps:
            print(f"   Found {len(gaps)} gaps in ID sequence:")
            for prev_id, current_id, gap_size in gaps:
                print(f"   Gap: {prev_id} → {current_id} (missing {gap_size} IDs)")
        else:
            print("   ✅ No gaps found in recent email IDs")
        
        # 3. Check for duplicate message_ids
        print(f"\n3. Duplicate message_id analysis:")
        cursor.execute("""
            SELECT message_id, COUNT(*) as count, 
                   MIN(id) as first_id, MAX(id) as last_id,
                   MIN(created_at) as first_date, MAX(created_at) as last_date
            FROM customer_emails 
            WHERE message_id IS NOT NULL
            GROUP BY message_id 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
            LIMIT 10
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"   Found {len(duplicates)} duplicate message_ids:")
            for dup in duplicates:
                msg_id, count, first_id, last_id, first_date, last_date = dup
                print(f"   Message-ID: {msg_id[:30]}...")
                print(f"     Count: {count}, IDs: {first_id} → {last_id}")
                print(f"     Dates: {first_date} → {last_date}")
        else:
            print("   ✅ No duplicate message_ids found")
        
        # 4. Check emails without message_id
        print(f"\n4. Emails without message_id:")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM customer_emails 
            WHERE message_id IS NULL
            AND created_at >= NOW() - INTERVAL '24 hours'
        """)
        
        null_msg_id_count = cursor.fetchone()[0]
        print(f"   Recent emails without message_id: {null_msg_id_count}")
        
        if null_msg_id_count > 0:
            cursor.execute("""
                SELECT id, sender, subject, created_at
                FROM customer_emails 
                WHERE message_id IS NULL
                AND created_at >= NOW() - INTERVAL '24 hours'
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            null_msg_emails = cursor.fetchall()
            print("   Examples:")
            for email in null_msg_emails:
                email_id, sender, subject, created_at = email
                print(f"     ID {email_id}: {subject[:40]}... ({created_at})")
        
        # 5. Check the ON CONFLICT behavior
        print(f"\n5. Database constraint analysis:")
        cursor.execute("""
            SELECT column_name, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'customer_emails' 
            AND column_name = 'message_id'
        """)
        
        msg_id_info = cursor.fetchone()
        if msg_id_info:
            column_name, is_nullable, column_default = msg_id_info
            print(f"   message_id column: nullable={is_nullable}, default={column_default}")
        
        # Check for unique constraint
        cursor.execute("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints 
            WHERE table_name = 'customer_emails' 
            AND constraint_type = 'UNIQUE'
        """)
        
        unique_constraints = cursor.fetchall()
        print(f"   Unique constraints: {len(unique_constraints)} found")
        for constraint in unique_constraints:
            print(f"     {constraint[0]}: {constraint[1]}")
        
        # 6. Summary and recommendations
        print(f"\n6. Summary and Recommendations:")
        
        if gaps:
            print(f"   ⚠️  ID gaps detected - this is normal with duplicate detection")
            print(f"   ✅ The gaps indicate duplicate emails were properly skipped")
        
        if duplicates:
            print(f"   ❌ Duplicate message_ids found - this should not happen")
            print(f"   🔧 Need to investigate why ON CONFLICT is not working")
        else:
            print(f"   ✅ No duplicate message_ids - duplicate detection working")
        
        if null_msg_id_count > 0:
            print(f"   ⚠️  {null_msg_id_count} emails without message_id")
            print(f"   📝 These use subject-based duplicate detection")
        
        print(f"\n🎯 Analysis completed!")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    analyze_email_sequence() 