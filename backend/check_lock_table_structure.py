#!/usr/bin/env python3
"""
Check email_processing_locks table structure
"""

from db_utils import get_db_conn

def check_table_structure():
    """Check the email_processing_locks table structure"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔍 Checking email_processing_locks table structure...")
        print("-" * 50)
        
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'email_processing_locks' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("📋 Table Structure:")
        for col in columns:
            print(f"  {col[0]}: {col[1]} (default: {col[2]}, nullable: {col[3]})")
        
        print("\n" + "-" * 50)
        
        # Check current locks with expiration info
        cursor.execute("""
            SELECT 
                user_id, 
                created_at, 
                expires_at,
                NOW() as current_time,
                expires_at - NOW() as time_until_expiry,
                CASE 
                    WHEN expires_at > NOW() THEN 'ACTIVE'
                    ELSE 'EXPIRED'
                END as status
            FROM email_processing_locks 
            ORDER BY created_at DESC
        """)
        
        locks = cursor.fetchall()
        if locks:
            print("🔒 Current Locks:")
            for lock in locks:
                user_id, created_at, expires_at, current_time, time_until_expiry, status = lock
                print(f"  👤 User: {user_id}")
                print(f"  🕐 Created: {created_at}")
                print(f"  ⏰ Expires: {expires_at}")
                print(f"  📊 Status: {status}")
                print(f"  ⏱️  Time until expiry: {time_until_expiry}")
                print()
        else:
            print("✅ No locks found in table")
            
        # Test the cleanup query
        print("🧪 Testing cleanup query...")
        cursor.execute("""
            SELECT COUNT(*) as total_locks,
                   COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as active_locks,
                   COUNT(CASE WHEN expires_at <= NOW() THEN 1 END) as expired_locks,
                   COUNT(CASE WHEN created_at < NOW() - INTERVAL '10 minutes' THEN 1 END) as stale_locks
            FROM email_processing_locks
        """)
        
        stats = cursor.fetchone()
        if stats:
            total, active, expired, stale = stats
            print(f"  📊 Total locks: {total}")
            print(f"  🔒 Active locks: {active}")
            print(f"  ⏰ Expired locks: {expired}")
            print(f"  🧹 Stale locks (>10min): {stale}")
        
    except Exception as e:
        print(f"❌ Error checking table structure: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_table_structure() 