#!/usr/bin/env python3
"""
Quick Performance Test
Tests basic database connection and simple queries
"""

import time
import sys
from config import get_db_conn

def test_connection_speed():
    """Test basic connection and simple operations"""
    print("🔍 Testing Connection and Basic Operations")
    print("=" * 50)
    
    # Test connection time
    print("\n🔌 Testing connection speed...")
    start_time = time.time()
    conn = get_db_conn()
    connection_time = time.time() - start_time
    print(f"  Connection time: {connection_time:.3f}s")
    
    if not conn:
        print("❌ Failed to get database connection")
        return False
    
    cursor = conn.cursor()
    
    try:
        # Test simple ping
        print("\n🏓 Testing database ping...")
        start_time = time.time()
        cursor.execute("SELECT 1")
        ping_time = time.time() - start_time
        print(f"  Ping time: {ping_time:.3f}s")
        
        # Test simple count without any joins
        print("\n📊 Testing simple COUNT...")
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        count = cursor.fetchone()[0]
        simple_count_time = time.time() - start_time
        print(f"  Simple COUNT time: {simple_count_time:.3f}s")
        print(f"  Total emails: {count}")
        
        # Test simple select without joins
        print("\n📄 Testing simple SELECT...")
        start_time = time.time()
        cursor.execute("SELECT id, sender, subject FROM customer_emails LIMIT 10")
        emails = cursor.fetchall()
        simple_select_time = time.time() - start_time
        print(f"  Simple SELECT time: {simple_select_time:.3f}s")
        print(f"  Emails returned: {len(emails)}")
        
        # Test the problematic join query
        print("\n📧 Testing JOIN query...")
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
            LIMIT 10
        """)
        join_emails = cursor.fetchall()
        join_time = time.time() - start_time
        print(f"  JOIN query time: {join_time:.3f}s")
        print(f"  Emails returned: {len(join_emails)}")
        
        # Performance analysis
        print("\n" + "=" * 50)
        print("📈 Performance Analysis:")
        print(f"  Connection: {connection_time:.3f}s")
        print(f"  Ping: {ping_time:.3f}s")
        print(f"  Simple COUNT: {simple_count_time:.3f}s")
        print(f"  Simple SELECT: {simple_select_time:.3f}s")
        print(f"  JOIN query: {join_time:.3f}s")
        
        # Identify bottleneck
        if connection_time > 0.1:
            print("⚠️ Connection is slow - check network/database")
        elif simple_count_time > 0.1:
            print("⚠️ Simple COUNT is slow - check table size/indexes")
        elif join_time > 0.2:
            print("⚠️ JOIN query is slow - check indexes on customer_email_replies")
        else:
            print("✅ All operations are fast")
            
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Run quick performance test"""
    print("🚀 Quick Performance Test")
    print("=" * 50)
    
    if not test_connection_speed():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Quick test completed!")

if __name__ == "__main__":
    main() 