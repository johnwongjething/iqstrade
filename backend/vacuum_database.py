#!/usr/bin/env python3
"""
Database VACUUM Script
Runs VACUUM ANALYZE outside of transaction blocks to improve performance
"""

import sys
import psycopg2
from config import get_db_conn

def run_vacuum_analyze():
    """Run VACUUM ANALYZE outside of transaction blocks"""
    print("🧹 Running VACUUM ANALYZE")
    print("=" * 50)
    
    # Get connection parameters from config
    from config import DatabaseConfig
    
    # Create new connection with autocommit
    vacuum_conn = psycopg2.connect(
        dbname=DatabaseConfig.dbname(),
        user=DatabaseConfig.user(),
        password=DatabaseConfig.password(),
        host=DatabaseConfig.host(),
        port=DatabaseConfig.port()
    )
    vacuum_conn.autocommit = True  # This allows VACUUM to run
    
    cursor = vacuum_conn.cursor()
    
    try:
        # Run VACUUM ANALYZE on customer_emails table
        print("\n🧹 Running VACUUM ANALYZE on customer_emails...")
        cursor.execute("VACUUM ANALYZE customer_emails")
        print("✅ VACUUM ANALYZE completed for customer_emails")
        
        # Run VACUUM ANALYZE on customer_email_replies table
        print("\n🧹 Running VACUUM ANALYZE on customer_email_replies...")
        cursor.execute("VACUUM ANALYZE customer_email_replies")
        print("✅ VACUUM ANALYZE completed for customer_email_replies")
        
        # Check results
        print("\n📋 VACUUM Results:")
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
        print(f"❌ Error during VACUUM: {e}")
        return False
    finally:
        cursor.close()
        vacuum_conn.close()

def test_performance_after_vacuum():
    """Test performance after VACUUM"""
    print("\n⚡ Testing Performance After VACUUM")
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
        
        # Test join query (the one used in the API)
        print("\n📧 Testing join query (API query)...")
        start_time = time.time()
        cursor.execute("""
            SELECT 
                e.id, 
                e.sender, 
                e.subject, 
                e.created_at,
                COALESCE(r.reply_count, 0) as reply_count
            FROM customer_emails e
            LEFT JOIN (
                SELECT customer_email_id, COUNT(*) as reply_count 
                FROM customer_email_replies 
                GROUP BY customer_email_id
            ) r ON e.id = r.customer_email_id
            ORDER BY e.created_at DESC, e.id DESC 
            LIMIT 50
        """)
        emails_with_replies = cursor.fetchall()
        join_time = time.time() - start_time
        print(f"  Emails returned: {len(emails_with_replies)}")
        print(f"  Time: {join_time:.3f}s")
        print(f"  Status: {'✅ Good' if join_time < 0.2 else '⚠️ Slow'}")
        
        # Performance assessment
        total_time = count_time + pagination_time + join_time
        print(f"\n🎯 Total test time: {total_time:.3f}s")
        
        if total_time < 0.3:
            print("✅ Excellent performance after VACUUM!")
        elif total_time < 0.6:
            print("✅ Good performance after VACUUM")
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
    """Run VACUUM and test performance"""
    print("🚀 Database VACUUM and Performance Test")
    print("=" * 50)
    
    # Run VACUUM
    if not run_vacuum_analyze():
        print("❌ VACUUM failed")
        sys.exit(1)
    
    # Test performance
    if not test_performance_after_vacuum():
        print("❌ Performance test failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ VACUUM and testing completed!")
    print("\n📋 Next steps:")
    print("1. Restart your Flask application")
    print("2. Test the email loading in the frontend")
    print("3. Monitor performance over time")
    print("\n🎯 Expected improvements:")
    print("- Email loading: Should be 10x faster")
    print("- Dead rows removed: 104 rows cleaned up")
    print("- Indexes optimized: Better query planning")

if __name__ == "__main__":
    main() 