#!/usr/bin/env python3
"""
Debug script to check why new emails are showing as "Sent"
"""

import psycopg2
import os
from datetime import datetime, timedelta
from config import get_db_conn

def debug_email_status():
    """Debug email status issues"""
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔍 Debugging Email Status Issues...")
        
        # 1. Check recent emails (last 24 hours)
        print("\n1. Recent emails (last 24 hours):")
        cursor.execute("""
            SELECT id, sender, subject, created_at 
            FROM customer_emails 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        recent_emails = cursor.fetchall()
        
        for email in recent_emails:
            email_id, sender, subject, created_at = email
            print(f"   Email {email_id}: {subject[:50]}... ({created_at})")
        
        # 2. Check if these emails have any replies
        if recent_emails:
            email_ids = [str(email[0]) for email in recent_emails]
            placeholders = ','.join(['%s'] * len(email_ids))
            
            cursor.execute(f"""
                SELECT 
                    customer_email_id, 
                    COUNT(*) as reply_count,
                    COUNT(CASE WHEN is_draft = FALSE THEN 1 END) as sent_count,
                    COUNT(CASE WHEN is_draft = TRUE THEN 1 END) as draft_count
                FROM customer_email_replies 
                WHERE customer_email_id IN ({placeholders})
                GROUP BY customer_email_id
            """, email_ids)
            
            reply_data = cursor.fetchall()
            print(f"\n2. Reply data for recent emails:")
            
            for row in reply_data:
                email_id, reply_count, sent_count, draft_count = row
                print(f"   Email {email_id}: {reply_count} total replies, {sent_count} sent, {draft_count} drafts")
                
                if sent_count > 0:
                    print(f"   ⚠️  Email {email_id} has {sent_count} sent replies - this is why it shows 'Sent'!")
                    
                    # Check what these sent replies are
                    cursor.execute("""
                        SELECT id, content, is_draft, created_at 
                        FROM customer_email_replies 
                        WHERE customer_email_id = %s AND is_draft = FALSE
                        ORDER BY created_at DESC
                    """, (email_id,))
                    
                    sent_replies = cursor.fetchall()
                    for reply in sent_replies:
                        reply_id, content, is_draft, created_at = reply
                        print(f"      Reply {reply_id}: {content[:50]}... ({created_at})")
        
        # 3. Check if there are any replies that shouldn't be there
        print(f"\n3. All replies in the system:")
        cursor.execute("""
            SELECT customer_email_id, COUNT(*) as reply_count, 
                   COUNT(CASE WHEN is_draft = FALSE THEN 1 END) as sent_count
            FROM customer_email_replies 
            GROUP BY customer_email_id
            ORDER BY sent_count DESC
            LIMIT 10
        """)
        
        all_replies = cursor.fetchall()
        for row in all_replies:
            email_id, reply_count, sent_count = row
            print(f"   Email {email_id}: {reply_count} total, {sent_count} sent")
        
        # 4. Check the exact query that the frontend uses
        print(f"\n4. Testing the exact frontend query:")
        if recent_emails:
            test_email_id = recent_emails[0][0]  # Use the most recent email
            
            cursor.execute("""
                SELECT 
                    customer_email_id, 
                    COUNT(*) as reply_count,
                    COUNT(CASE WHEN is_draft = FALSE THEN 1 END) as sent_count
                FROM customer_email_replies 
                WHERE customer_email_id = %s
                GROUP BY customer_email_id
            """, (test_email_id,))
            
            result = cursor.fetchone()
            if result:
                email_id, reply_count, sent_count = result
                print(f"   Email {email_id}: reply_count={reply_count}, sent_count={sent_count}")
                print(f"   has_replies = {reply_count > 0}")
                print(f"   has_sent_replies = {sent_count > 0}")
                
                if sent_count > 0:
                    print(f"   ❌ This email will show as 'Sent' because sent_count > 0")
                elif reply_count > 0:
                    print(f"   ✅ This email will show as 'AI Reply Ready' because has_replies=true, has_sent_replies=false")
                else:
                    print(f"   ✅ This email will show as 'No AI Reply' because has_replies=false")
            else:
                print(f"   ✅ Email {test_email_id} has no replies - will show as 'No AI Reply'")
        
        print(f"\n🎯 Debug completed!")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    debug_email_status() 