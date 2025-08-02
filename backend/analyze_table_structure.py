#!/usr/bin/env python3
"""
Table Structure Analysis
Analyzes the customer_emails table structure to understand performance issues
"""

import sys
from config import get_db_conn

def analyze_table_structure():
    """Analyze the customer_emails table structure"""
    print("🔍 Analyzing Table Structure")
    print("=" * 50)
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Check table size and row count
        print("\n📊 Table Statistics:")
        cursor.execute("""
            SELECT 
                schemaname,
                relname as tablename,
                n_tup_ins as inserts,
                n_tup_upd as updates,
                n_tup_del as deletes,
                n_live_tup as live_rows,
                n_dead_tup as dead_rows,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables 
            WHERE relname = 'customer_emails'
        """)
        
        stats = cursor.fetchone()
        if stats:
            print(f"  Table: {stats[0]}.{stats[1]}")
            print(f"  Live rows: {stats[5]:,}")
            print(f"  Dead rows: {stats[6]:,}")
            print(f"  Last vacuum: {stats[7]}")
            print(f"  Last analyze: {stats[9]}")
        
        # Check table size
        cursor.execute("""
            SELECT 
                pg_size_pretty(pg_total_relation_size('customer_emails')) as total_size,
                pg_size_pretty(pg_relation_size('customer_emails')) as table_size,
                pg_size_pretty(pg_total_relation_size('customer_emails') - pg_relation_size('customer_emails')) as index_size
        """)
        
        size_info = cursor.fetchone()
        if size_info:
            print(f"  Total size: {size_info[0]}")
            print(f"  Table size: {size_info[1]}")
            print(f"  Index size: {size_info[2]}")
        
        # Check column statistics
        print("\n📋 Column Statistics:")
        cursor.execute("""
            SELECT 
                attname as column_name,
                n_distinct,
                most_common_vals,
                most_common_freqs
            FROM pg_stats 
            WHERE tablename = 'customer_emails'
            ORDER BY attname
        """)
        
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]}: {col[1]} distinct values")
        
        # Check if table needs vacuum/analyze
        print("\n🔧 Maintenance Status:")
        cursor.execute("""
            SELECT 
                schemaname,
                relname as tablename,
                last_vacuum,
                last_analyze,
                CASE 
                    WHEN n_dead_tup > n_live_tup * 0.1 THEN 'NEEDS VACUUM'
                    ELSE 'OK'
                END as vacuum_status,
                CASE 
                    WHEN last_analyze IS NULL OR last_analyze < NOW() - INTERVAL '1 day' THEN 'NEEDS ANALYZE'
                    ELSE 'OK'
                END as analyze_status
            FROM pg_stat_user_tables 
            WHERE relname = 'customer_emails'
        """)
        
        maintenance = cursor.fetchone()
        if maintenance:
            print(f"  Vacuum status: {maintenance[4]}")
            print(f"  Analyze status: {maintenance[5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing table structure: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def check_index_effectiveness():
    """Check if indexes are being used effectively"""
    print("\n🔍 Checking Index Effectiveness")
    print("=" * 50)
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Test different query patterns
        print("\n📊 Testing Query Patterns:")
        
        # Test 1: Simple count with EXPLAIN
        print("\n1. Simple COUNT query:")
        cursor.execute("""
            EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
            SELECT COUNT(*) FROM customer_emails
        """)
        
        plan = cursor.fetchall()
        for row in plan:
            print(f"  {row[0]}")
        
        # Test 2: ORDER BY created_at
        print("\n2. ORDER BY created_at DESC:")
        cursor.execute("""
            EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
            SELECT id, created_at 
            FROM customer_emails 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        plan = cursor.fetchall()
        for row in plan:
            print(f"  {row[0]}")
        
        # Test 3: Filter by sender
        print("\n3. Filter by sender:")
        cursor.execute("""
            EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
            SELECT id, sender 
            FROM customer_emails 
            WHERE sender ILIKE '%test%'
            LIMIT 10
        """)
        
        plan = cursor.fetchall()
        for row in plan:
            print(f"  {row[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking index effectiveness: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def suggest_optimizations():
    """Suggest performance optimizations"""
    print("\n💡 Performance Optimization Suggestions")
    print("=" * 50)
    
    print("\n1. **Immediate Actions:**")
    print("   - Run VACUUM ANALYZE on customer_emails table")
    print("   - Check if table statistics are up to date")
    print("   - Consider partitioning for large tables")
    
    print("\n2. **Query Optimizations:**")
    print("   - Use cursor-based pagination instead of OFFSET")
    print("   - Implement caching for frequently accessed data")
    print("   - Consider materialized views for complex queries")
    
    print("\n3. **Index Optimizations:**")
    print("   - Review index usage patterns")
    print("   - Consider partial indexes for filtered queries")
    print("   - Remove unused indexes")
    
    print("\n4. **Application Level:**")
    print("   - Implement connection pooling")
    print("   - Use background processing for heavy operations")
    print("   - Add caching layer (Redis)")

def main():
    """Run table structure analysis"""
    print("🚀 Table Structure Analysis")
    print("=" * 50)
    
    if not analyze_table_structure():
        sys.exit(1)
    
    if not check_index_effectiveness():
        sys.exit(1)
    
    suggest_optimizations()
    
    print("\n" + "=" * 50)
    print("✅ Analysis completed!")

if __name__ == "__main__":
    main() 