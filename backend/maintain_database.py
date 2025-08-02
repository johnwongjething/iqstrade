#!/usr/bin/env python3
"""
Database Maintenance Script
Performs VACUUM ANALYZE and other maintenance tasks to improve performance
"""

import sys
from config import get_db_conn

def run_maintenance():
    """Run database maintenance tasks"""
    print("🔧 Running Database Maintenance")
    print("=" * 50)
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Run VACUUM ANALYZE on customer_emails table
        print("\n🧹 Running VACUUM ANALYZE on customer_emails...")
        cursor.execute("VACUUM ANALYZE customer_emails")
        print("✅ VACUUM ANALYZE completed")
        
        # Run VACUUM ANALYZE on customer_email_replies table
        print("\n🧹 Running VACUUM ANALYZE on customer_email_replies...")
        cursor.execute("VACUUM ANALYZE customer_email_replies")
        print("✅ VACUUM ANALYZE completed")
        
        # Update table statistics
        print("\n📊 Updating table statistics...")
        cursor.execute("ANALYZE customer_emails")
        cursor.execute("ANALYZE customer_email_replies")
        print("✅ Table statistics updated")
        
        # Check maintenance results
        print("\n📋 Maintenance Results:")
        cursor.execute("""
            SELECT 
                schemaname,
                relname as tablename,
                last_vacuum,
                last_analyze,
                n_live_tup as live_rows,
                n_dead_tup as dead_rows
            FROM pg_stat_user_tables 
            WHERE relname IN ('customer_emails', 'customer_email_replies')
            ORDER BY relname
        """)
        
        results = cursor.fetchall()
        for result in results:
            print(f"  {result[1]}:")
            print(f"    - Live rows: {result[4]:,}")
            print(f"    - Dead rows: {result[5]:,}")
            print(f"    - Last vacuum: {result[2]}")
            print(f"    - Last analyze: {result[3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during maintenance: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def test_performance_after_maintenance():
    """Test performance after maintenance"""
    print("\n⚡ Testing Performance After Maintenance")
    print("=" * 50)
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        import time
        
        # Test count query
        print("\n📊 Testing COUNT query...")
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        count = cursor.fetchone()[0]
        count_time = time.time() - start_time
        print(f"  Total emails: {count}")
        print(f"  Time: {count_time:.3f}s")
        print(f"  Status: {'✅ Good' if count_time < 0.1 else '⚠️ Slow'}")
        
        # Test pagination query
        print("\n📄 Testing pagination query...")
        start_time = time.time()
        cursor.execute("""
            SELECT id, sender, subject, created_at 
            FROM customer_emails 
            ORDER BY created_at DESC, id DESC 
            LIMIT 50
        """)
        emails = cursor.fetchall()
        pagination_time = time.time() - start_time
        print(f"  Emails returned: {len(emails)}")
        print(f"  Time: {pagination_time:.3f}s")
        print(f"  Status: {'✅ Good' if pagination_time < 0.1 else '⚠️ Slow'}")
        
        # Performance assessment
        total_time = count_time + pagination_time
        print(f"\n🎯 Total test time: {total_time:.3f}s")
        
        if total_time < 0.2:
            print("✅ Excellent performance after maintenance!")
        elif total_time < 0.5:
            print("✅ Good performance after maintenance")
        else:
            print("⚠️ Performance still needs improvement")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing performance: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Run database maintenance and test performance"""
    print("🚀 Database Maintenance and Performance Test")
    print("=" * 50)
    
    # Run maintenance
    if not run_maintenance():
        print("❌ Maintenance failed")
        sys.exit(1)
    
    # Test performance
    if not test_performance_after_maintenance():
        print("❌ Performance test failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Maintenance and testing completed!")
    print("\n📋 Next steps:")
    print("1. Restart your Flask application")
    print("2. Test the email loading in the frontend")
    print("3. Monitor performance over time")

if __name__ == "__main__":
    main() 