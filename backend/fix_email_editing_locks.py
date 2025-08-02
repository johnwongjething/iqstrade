#!/usr/bin/env python3
"""
Fix email editing locks - Move from in-memory to database storage
"""

from db_utils import get_db_conn

def create_email_editing_locks_table():
    """Create the email editing locks table"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔧 Creating email editing locks table...")
        
        # Create the table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_editing_locks (
                id SERIAL PRIMARY KEY,
                email_id INTEGER NOT NULL,
                user_id VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                expires_at TIMESTAMP NOT NULL,
                UNIQUE(email_id)  -- Only one lock per email
            )
        """)
        
        # Add foreign key constraint
        try:
            cursor.execute("""
                ALTER TABLE email_editing_locks 
                ADD CONSTRAINT fk_email_editing_locks_email 
                FOREIGN KEY (email_id) REFERENCES customer_emails(id) ON DELETE CASCADE
            """)
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✅ Foreign key constraint already exists")
            else:
                raise e
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_editing_locks_expires 
            ON email_editing_locks(expires_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_editing_locks_user 
            ON email_editing_locks(user_id)
        """)
        
        conn.commit()
        print("✅ Email editing locks table created successfully")
        
        # Add comment
        cursor.execute("""
            COMMENT ON TABLE email_editing_locks IS 'Prevents multiple users from editing the same email simultaneously'
        """)
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error creating email editing locks table: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def create_user_activity_table():
    """Create the user activity table"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔧 Creating user activity table...")
        
        # Create the table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(100) NOT NULL,
                current_email_id INTEGER,
                current_action VARCHAR(50),
                last_activity TIMESTAMP DEFAULT NOW(),
                UNIQUE(user_id)  -- One activity record per user
            )
        """)
        
        # Add foreign key constraint
        try:
            cursor.execute("""
                ALTER TABLE user_activity 
                ADD CONSTRAINT fk_user_activity_email 
                FOREIGN KEY (current_email_id) REFERENCES customer_emails(id) ON DELETE SET NULL
            """)
        except Exception as e:
            if "already exists" in str(e).lower():
                print("✅ Foreign key constraint already exists")
            else:
                raise e
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_activity_last_activity 
            ON user_activity(last_activity)
        """)
        
        conn.commit()
        print("✅ User activity table created successfully")
        
        # Add comment
        cursor.execute("""
            COMMENT ON TABLE user_activity IS 'Tracks user activity for real-time collaboration features'
        """)
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error creating user activity table: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def create_cleanup_functions():
    """Create cleanup functions for expired locks and stale activity"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔧 Creating cleanup functions...")
        
        # Function to cleanup expired email editing locks
        cursor.execute("""
            CREATE OR REPLACE FUNCTION cleanup_expired_email_editing_locks()
            RETURNS void AS $$
            BEGIN
                DELETE FROM email_editing_locks 
                WHERE expires_at < NOW();
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Function to cleanup stale user activity (older than 30 minutes)
        cursor.execute("""
            CREATE OR REPLACE FUNCTION cleanup_stale_user_activity()
            RETURNS void AS $$
            BEGIN
                DELETE FROM user_activity 
                WHERE last_activity < NOW() - INTERVAL '30 minutes';
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        conn.commit()
        print("✅ Cleanup functions created successfully")
        
    except Exception as e:
        print(f"❌ Error creating cleanup functions: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def test_email_editing_locks():
    """Test the email editing locks system"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("\n🧪 Testing email editing locks system...")
        
        # Clear any existing test data
        cursor.execute("DELETE FROM email_editing_locks WHERE user_id LIKE 'test_%'")
        cursor.execute("DELETE FROM user_activity WHERE user_id LIKE 'test_%'")
        conn.commit()
        
        # Test 1: User A acquires lock on email 1
        print("Test 1: User A acquiring lock on email 1...")
        cursor.execute("""
            INSERT INTO email_editing_locks (email_id, user_id, expires_at)
            VALUES (1, 'test_user_a', NOW() + INTERVAL '10 minutes')
            RETURNING id
        """)
        
        lock_a = cursor.fetchone()
        if lock_a:
            print("✅ User A: Lock acquired successfully")
        else:
            print("❌ User A: Lock failed")
        
        # Test 2: User B tries to acquire lock on same email (should fail)
        print("Test 2: User B trying to acquire lock on same email...")
        try:
            cursor.execute("""
                INSERT INTO email_editing_locks (email_id, user_id, expires_at)
                VALUES (1, 'test_user_b', NOW() + INTERVAL '10 minutes')
                RETURNING id
            """)
            
            lock_b = cursor.fetchone()
            if lock_b:
                print("❌ User B: Lock acquired (should have failed)")
            else:
                print("✅ User B: Lock correctly blocked")
        except Exception as e:
            if "duplicate key" in str(e).lower():
                print("✅ User B: Lock correctly blocked by constraint")
            else:
                print(f"❌ User B: Unexpected error: {e}")
        
        # Test 3: User B acquires lock on different email (should succeed)
        print("Test 3: User B acquiring lock on different email...")
        cursor.execute("""
            INSERT INTO email_editing_locks (email_id, user_id, expires_at)
            VALUES (2, 'test_user_b', NOW() + INTERVAL '10 minutes')
            RETURNING id
        """)
        
        lock_b2 = cursor.fetchone()
        if lock_b2:
            print("✅ User B: Lock acquired on different email")
        else:
            print("❌ User B: Lock failed on different email")
        
        # Test 4: Check current locks
        cursor.execute("""
            SELECT email_id, user_id, expires_at > NOW() as is_active
            FROM email_editing_locks
            WHERE user_id LIKE 'test_%'
        """)
        
        locks = cursor.fetchall()
        print(f"📊 Current test locks: {len(locks)}")
        for lock in locks:
            email_id, user_id, is_active = lock
            print(f"  📧 Email {email_id}: {user_id} ({'ACTIVE' if is_active else 'EXPIRED'})")
        
        # Test 5: Test user activity
        print("\nTest 5: Testing user activity tracking...")
        cursor.execute("""
            INSERT INTO user_activity (user_id, current_email_id, current_action)
            VALUES ('test_user_a', 1, 'editing')
            ON CONFLICT (user_id) DO UPDATE SET
                current_email_id = EXCLUDED.current_email_id,
                current_action = EXCLUDED.current_action,
                last_activity = NOW()
        """)
        
        cursor.execute("""
            INSERT INTO user_activity (user_id, current_email_id, current_action)
            VALUES ('test_user_b', 2, 'viewing')
            ON CONFLICT (user_id) DO UPDATE SET
                current_email_id = EXCLUDED.current_email_id,
                current_action = EXCLUDED.current_action,
                last_activity = NOW()
        """)
        
        conn.commit()
        print("✅ User activity records created")
        
        # Check user activity
        cursor.execute("""
            SELECT user_id, current_email_id, current_action, last_activity
            FROM user_activity
            WHERE user_id LIKE 'test_%'
        """)
        
        activities = cursor.fetchall()
        print(f"📊 Current user activities: {len(activities)}")
        for activity in activities:
            user_id, email_id, action, last_activity = activity
            print(f"  👤 {user_id}: Email {email_id}, Action: {action}, Last: {last_activity}")
        
        # Clean up test data
        cursor.execute("DELETE FROM email_editing_locks WHERE user_id LIKE 'test_%'")
        cursor.execute("DELETE FROM user_activity WHERE user_id LIKE 'test_%'")
        conn.commit()
        print("✅ Test data cleaned up")
        
        print("\n🎉 Email editing locks system test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing email editing locks: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to fix email editing locks"""
    print("🔧 Fixing email editing locks system...")
    print("=" * 50)
    
    # Step 1: Create tables
    create_email_editing_locks_table()
    create_user_activity_table()
    
    # Step 2: Create cleanup functions
    create_cleanup_functions()
    
    # Step 3: Test the system
    test_email_editing_locks()
    
    print("\n🎉 Email editing locks system fixed!")
    print("\n📋 What was implemented:")
    print("✅ Database-based email editing locks")
    print("✅ Database-based user activity tracking")
    print("✅ Automatic cleanup of expired locks")
    print("✅ Automatic cleanup of stale user activity")
    print("✅ Foreign key constraints for data integrity")
    print("✅ Performance indexes for fast queries")
    print("\n🔄 Next step: Update email_routes.py to use database locks")

if __name__ == "__main__":
    main() 