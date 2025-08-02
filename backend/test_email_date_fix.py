#!/usr/bin/env python3
"""
Test script to verify email date fix works correctly
"""

from config import get_db_conn
from datetime import datetime, timedelta

def test_email_date_fix():
    """Test that email dates are now being stored correctly"""
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🧪 Testing Email Date Fix...")
        
        # 1. Check recent emails and their dates
        print("\n1. Recent emails with their dates:")
        cursor.execute("""
            SELECT id, sender, subject, created_at, message_id
            FROM customer_emails 
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        recent_emails = cursor.fetchall()
        if recent_emails:
            print("   ID    | Created At          | Subject")
            print("   ------|---------------------|------------------")
            for email in recent_emails:
                email_id, sender, subject, created_at, message_id = email
                print(f"   {email_id:6d} | {created_at} | {subject[:30]}...")
        
        # 2. Check if dates are properly distributed (not all the same)
        print(f"\n2. Date distribution analysis:")
        if recent_emails:
            dates = [email[3] for email in recent_emails]
            unique_dates = len(set(dates))
            total_emails = len(dates)
            
            print(f"   Total emails: {total_emails}")
            print(f"   Unique dates: {unique_dates}")
            
            if unique_dates > 1:
                print(f"   ✅ Good! Emails have different dates (not all processed at same time)")
            else:
                print(f"   ⚠️  All emails have the same date - might still be using processing time")
            
            # Show time differences
            if len(dates) >= 2:
                time_diff = abs(dates[0] - dates[1])
                print(f"   Time difference between newest emails: {time_diff}")
        
        # 3. Check for emails with message_id vs without
        print(f"\n3. Message-ID analysis:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN message_id IS NOT NULL THEN 1 END) as with_msg_id,
                COUNT(CASE WHEN message_id IS NULL THEN 1 END) as without_msg_id
            FROM customer_emails 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """)
        
        msg_id_stats = cursor.fetchone()
        if msg_id_stats:
            total, with_msg_id, without_msg_id = msg_id_stats
            print(f"   Recent emails: {total}")
            print(f"   With Message-ID: {with_msg_id}")
            print(f"   Without Message-ID: {without_msg_id}")
        
        # 4. Test the fix by checking if newer emails appear first
        print(f"\n4. Order verification:")
        if recent_emails:
            newest_email = recent_emails[0]
            oldest_email = recent_emails[-1]
            
            print(f"   Newest email: ID {newest_email[0]} at {newest_email[3]}")
            print(f"   Oldest email: ID {oldest_email[0]} at {oldest_email[3]}")
            
            if newest_email[3] > oldest_email[3]:
                print(f"   ✅ Correct! Newest email has newer date")
            else:
                print(f"   ❌ Issue! Newest email has older date")
        
        # 5. Check for any remaining issues
        print(f"\n5. Potential issues:")
        
        # Check for emails with future dates (timezone issues)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_emails 
            WHERE created_at > NOW() + INTERVAL '1 hour'
        """)
        
        future_emails = cursor.fetchone()[0]
        if future_emails > 0:
            print(f"   ⚠️  Found {future_emails} emails with future dates (timezone issue)")
        else:
            print(f"   ✅ No emails with future dates")
        
        # Check for emails with very old dates
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_emails 
            WHERE created_at < NOW() - INTERVAL '30 days'
        """)
        
        old_emails = cursor.fetchone()[0]
        if old_emails > 0:
            print(f"   📅 Found {old_emails} emails older than 30 days")
        else:
            print(f"   ✅ All emails are recent")
        
        print(f"\n🎯 Email date fix test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_email_date_fix() 