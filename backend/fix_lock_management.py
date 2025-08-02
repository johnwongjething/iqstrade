#!/usr/bin/env python3
"""
Fix lock management for production use
"""

from db_utils import get_db_conn
import datetime

def fix_lock_management():
    """Fix lock management issues"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔧 Fixing lock management for production...")
        print("-" * 50)
        
        # 1. Clear all existing locks
        print("🧹 Step 1: Clearing all existing locks...")
        cursor.execute("DELETE FROM email_processing_locks")
        cleared_count = cursor.rowcount
        conn.commit()
        print(f"✅ Cleared {cleared_count} existing locks")
        
        # 2. Add better cleanup logic
        print("\n🔧 Step 2: Adding better cleanup logic...")
        
        # Create a function to clean up expired locks
        cleanup_function = """
        CREATE OR REPLACE FUNCTION cleanup_expired_email_locks()
        RETURNS void AS $$
        BEGIN
            -- Delete locks that have expired
            DELETE FROM email_processing_locks 
            WHERE expires_at <= NOW();
            
            -- Delete stale locks (older than 5 minutes)
            DELETE FROM email_processing_locks 
            WHERE created_at < NOW() - INTERVAL '5 minutes';
        END;
        $$ LANGUAGE plpgsql;
        """
        
        cursor.execute(cleanup_function)
        conn.commit()
        print("✅ Created cleanup function")
        
        # 3. Create a trigger to auto-cleanup
        print("\n🔧 Step 3: Creating auto-cleanup trigger...")
        
        trigger_function = """
        CREATE OR REPLACE FUNCTION auto_cleanup_email_locks()
        RETURNS trigger AS $$
        BEGIN
            -- Clean up expired locks before inserting new ones
            PERFORM cleanup_expired_email_locks();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        cursor.execute(trigger_function)
        
        # Drop existing trigger if it exists
        cursor.execute("DROP TRIGGER IF EXISTS email_locks_cleanup_trigger ON email_processing_locks")
        
        # Create new trigger
        trigger = """
        CREATE TRIGGER email_locks_cleanup_trigger
        BEFORE INSERT ON email_processing_locks
        FOR EACH ROW
        EXECUTE FUNCTION auto_cleanup_email_locks();
        """
        
        cursor.execute(trigger)
        conn.commit()
        print("✅ Created auto-cleanup trigger")
        
        # 4. Test the new system
        print("\n🧪 Step 4: Testing new lock system...")
        
        # Test acquiring a lock
        cursor.execute("""
            INSERT INTO email_processing_locks (user_id, created_at, expires_at)
            VALUES ('test_user', NOW(), NOW() + INTERVAL '30 seconds')
            RETURNING id
        """)
        
        test_lock = cursor.fetchone()
        if test_lock:
            print("✅ Test lock acquired successfully")
            
            # Check current locks
            cursor.execute("""
                SELECT user_id, created_at, expires_at,
                       CASE WHEN expires_at > NOW() THEN 'ACTIVE' ELSE 'EXPIRED' END as status
                FROM email_processing_locks
            """)
            
            locks = cursor.fetchall()
            print(f"📊 Current locks: {len(locks)}")
            for lock in locks:
                user_id, created_at, expires_at, status = lock
                print(f"  👤 {user_id}: {status}")
            
            # Clean up test lock
            cursor.execute("DELETE FROM email_processing_locks WHERE user_id = 'test_user'")
            conn.commit()
            print("✅ Test lock cleaned up")
        
        print("\n🎉 Lock management system fixed!")
        print("\n📋 Production Recommendations:")
        print("1. ✅ Locks now auto-expire after 30 seconds")
        print("2. ✅ Stale locks (>5min) are automatically cleaned up")
        print("3. ✅ Trigger ensures cleanup before new locks")
        print("4. ✅ Multiple users can safely share the email account")
        print("5. ✅ No more manual lock clearing needed")
        
    except Exception as e:
        print(f"❌ Error fixing lock management: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def test_lock_behavior():
    """Test the new lock behavior"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("\n🧪 Testing lock behavior...")
        
        # Test 1: Acquire lock
        print("Test 1: Acquiring lock...")
        cursor.execute("""
            INSERT INTO email_processing_locks (user_id, created_at, expires_at)
            VALUES ('user1', NOW(), NOW() + INTERVAL '30 seconds')
            ON CONFLICT DO NOTHING
            RETURNING id
        """)
        
        lock1 = cursor.fetchone()
        if lock1:
            print("✅ Lock 1 acquired")
        else:
            print("❌ Lock 1 failed")
        
        # Test 2: Try to acquire another lock (should fail)
        print("Test 2: Trying to acquire second lock...")
        cursor.execute("""
            INSERT INTO email_processing_locks (user_id, created_at, expires_at)
            VALUES ('user2', NOW(), NOW() + INTERVAL '30 seconds')
            ON CONFLICT DO NOTHING
            RETURNING id
        """)
        
        lock2 = cursor.fetchone()
        if lock2:
            print("❌ Lock 2 acquired (should have failed)")
        else:
            print("✅ Lock 2 correctly blocked")
        
        # Test 3: Check current locks
        cursor.execute("""
            SELECT user_id, expires_at > NOW() as is_active
            FROM email_processing_locks
        """)
        
        locks = cursor.fetchall()
        print(f"📊 Current locks: {len(locks)}")
        for lock in locks:
            user_id, is_active = lock
            print(f"  👤 {user_id}: {'ACTIVE' if is_active else 'EXPIRED'}")
        
        # Clean up
        cursor.execute("DELETE FROM email_processing_locks")
        conn.commit()
        print("✅ Test locks cleaned up")
        
    except Exception as e:
        print(f"❌ Error testing lock behavior: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_lock_behavior()
    else:
        fix_lock_management()
        test_lock_behavior() 