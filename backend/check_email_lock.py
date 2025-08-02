#!/usr/bin/env python3
"""
Check and clear email processing locks
"""

from db_utils import get_db_conn
import datetime

def check_email_locks():
    """Check current email processing locks"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔍 Checking email processing locks...")
        print("-" * 50)
        
        # Check database locks
        cursor.execute("""
            SELECT user_id, created_at, expires_at, 
                   EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_old
            FROM email_processing_locks 
            WHERE expires_at > NOW()
            ORDER BY created_at DESC
        """)
        
        db_locks = cursor.fetchall()
        
        if db_locks:
            print("📋 Active Database Locks:")
            for lock in db_locks:
                user_id, created_at, expires_at, minutes_old = lock
                print(f"  👤 User: {user_id}")
                print(f"  🕐 Created: {created_at}")
                print(f"  ⏰ Expires: {expires_at}")
                print(f"  📊 Age: {minutes_old:.1f} minutes old")
                print()
        else:
            print("✅ No active database locks found")
        
        # Check for stale locks (older than 10 minutes)
        cursor.execute("""
            SELECT user_id, created_at, expires_at,
                   EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_old
            FROM email_processing_locks 
            WHERE created_at < NOW() - INTERVAL '10 minutes'
            ORDER BY created_at DESC
        """)
        
        stale_locks = cursor.fetchall()
        
        if stale_locks:
            print("⚠️  Stale Locks (older than 10 minutes):")
            for lock in stale_locks:
                user_id, created_at, expires_at, minutes_old = lock
                print(f"  👤 User: {user_id}")
                print(f"  🕐 Created: {created_at}")
                print(f"  📊 Age: {minutes_old:.1f} minutes old")
                print()
        else:
            print("✅ No stale locks found")
            
    except Exception as e:
        print(f"❌ Error checking locks: {e}")
    finally:
        cursor.close()
        conn.close()

def clear_all_locks():
    """Clear all email processing locks"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🧹 Clearing all email processing locks...")
        
        cursor.execute("DELETE FROM email_processing_locks")
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ Cleared {deleted_count} locks")
        
    except Exception as e:
        print(f"❌ Error clearing locks: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def clear_stale_locks():
    """Clear only stale locks (older than 10 minutes)"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🧹 Clearing stale email processing locks...")
        
        cursor.execute("""
            DELETE FROM email_processing_locks 
            WHERE created_at < NOW() - INTERVAL '10 minutes'
        """)
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"✅ Cleared {deleted_count} stale locks")
        
    except Exception as e:
        print(f"❌ Error clearing stale locks: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        
        if action == "clear":
            clear_all_locks()
        elif action == "clear-stale":
            clear_stale_locks()
        else:
            print("Usage: python check_email_lock.py [check|clear|clear-stale]")
            print("  check: Check current locks (default)")
            print("  clear: Clear all locks")
            print("  clear-stale: Clear only stale locks")
    else:
        check_email_locks()
        print("\n💡 To clear all locks: python check_email_lock.py clear")
        print("💡 To clear stale locks: python check_email_lock.py clear-stale") 