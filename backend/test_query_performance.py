#!/usr/bin/env python3
"""
Query Performance Test Script
Tests and analyzes the performance of email queries
"""

import time
import sys
from config import get_db_conn

def test_query_performance():
    """Test various query performance scenarios"""
    print("🔍 Testing Query Performance")
    print("=" * 50)
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Test 1: Simple count
        print("\n📊 Test 1: Simple COUNT query")
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        count = cursor.fetchone()[0]
        count_time = time.time() - start_time
        print(f"  Total emails: {count}")
        print(f"  Time: {count_time:.3f}s")
        print(f"  Status: {'✅ Good' if count_time < 0.1 else '⚠️ Slow'}")
        
        # Test 2: Paginated query with ORDER BY created_at
        print("\n📄 Test 2: Paginated query (ORDER BY created_at DESC)")
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
        
        # Test 3: Query with reply count
        print("\n📧 Test 3: Query with reply count (LEFT JOIN)")
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
        
        # Test 4: Filtered query
        print("\n🔍 Test 4: Filtered query (sender LIKE)")
        start_time = time.time()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_emails 
            WHERE sender ILIKE '%test%'
        """)
        filtered_count = cursor.fetchone()[0]
        filter_time = time.time() - start_time
        print(f"  Filtered count: {filtered_count}")
        print(f"  Time: {filter_time:.3f}s")
        print(f"  Status: {'✅ Good' if filter_time < 0.1 else '⚠️ Slow'}")
        
        # Test 5: Date range query
        print("\n📅 Test 5: Date range query")
        start_time = time.time()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_emails 
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        recent_count = cursor.fetchone()[0]
        date_time = time.time() - start_time
        print(f"  Recent emails (7 days): {recent_count}")
        print(f"  Time: {date_time:.3f}s")
        print(f"  Status: {'✅ Good' if date_time < 0.1 else '⚠️ Slow'}")
        
        # Performance summary
        print("\n" + "=" * 50)
        print("📈 Performance Summary:")
        print(f"  Count Query: {count_time:.3f}s {'✅' if count_time < 0.1 else '⚠️'}")
        print(f"  Pagination Query: {pagination_time:.3f}s {'✅' if pagination_time < 0.1 else '⚠️'}")
        print(f"  Join Query: {join_time:.3f}s {'✅' if join_time < 0.2 else '⚠️'}")
        print(f"  Filter Query: {filter_time:.3f}s {'✅' if filter_time < 0.1 else '⚠️'}")
        print(f"  Date Query: {date_time:.3f}s {'✅' if date_time < 0.1 else '⚠️'}")
        
        # Overall assessment
        total_time = count_time + pagination_time + join_time + filter_time + date_time
        print(f"\n🎯 Overall Performance: {total_time:.3f}s total")
        
        if total_time < 0.5:
            print("✅ Excellent performance!")
        elif total_time < 1.0:
            print("✅ Good performance")
        else:
            print("⚠️ Performance needs improvement")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing performance: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def analyze_index_usage():
    """Analyze which indexes are being used"""
    print("\n🔍 Analyzing Index Usage")
    print("=" * 50)
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Check index usage statistics
        cursor.execute("""
            SELECT 
                schemaname,
                relname as tablename,
                indexrelname as indexname,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE relname IN ('customer_emails', 'customer_email_replies')
            ORDER BY idx_scan DESC
        """)
        
        indexes = cursor.fetchall()
        
        if indexes:
            print("📊 Index Usage Statistics:")
            for index in indexes:
                schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch = index
                print(f"  {tablename}.{indexname}:")
                print(f"    - Scans: {idx_scan}")
                print(f"    - Tuples read: {idx_tup_read}")
                print(f"    - Tuples fetched: {idx_tup_fetch}")
        else:
            print("⚠️ No index usage data found")
            
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing index usage: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def explain_query_plan():
    """Show query execution plans"""
    print("\n📋 Query Execution Plans")
    print("=" * 50)
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Test the main pagination query
        print("\n📄 Main Pagination Query Plan:")
        cursor.execute("""
            EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
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
        
        plan = cursor.fetchall()
        for row in plan:
            print(f"  {row[0]}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error explaining query plan: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Run all performance tests"""
    print("🚀 Query Performance Analysis")
    print("=" * 50)
    
    # Run performance tests
    if not test_query_performance():
        sys.exit(1)
    
    # Analyze index usage
    if not analyze_index_usage():
        sys.exit(1)
    
    # Show query plans
    if not explain_query_plan():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Performance analysis completed!")
    print("\n💡 Recommendations:")
    print("1. If queries are slow, check if indexes are being used")
    print("2. Consider adding more specific indexes for common filters")
    print("3. Monitor query performance over time")

if __name__ == "__main__":
    main() 