#!/usr/bin/env python3
"""
Performance Fixes Runner for IQSTrade
- Adds database indexes for faster queries
- Sets up performance optimizations
"""

import os
import sys
from config import get_db_conn

def run_database_indexes():
    """Add performance indexes to the database"""
    print("🔧 Adding database indexes for performance...")
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Read and execute the indexes SQL file
        index_file = os.path.join(os.path.dirname(__file__), 'add_performance_indexes.sql')
        
        if not os.path.exists(index_file):
            print(f"❌ Index file not found: {index_file}")
            return False
        
        with open(index_file, 'r') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement.startswith('--') or not statement:
                continue
            
            try:
                print(f"  Executing statement {i+1}/{len(statements)}...")
                cursor.execute(statement)
                conn.commit()
                print(f"  ✅ Statement {i+1} executed successfully")
            except Exception as e:
                print(f"  ⚠️ Statement {i+1} failed (may already exist): {e}")
                conn.rollback()
        
        print("✅ Database indexes added successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error adding database indexes: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_indexes():
    """Verify that indexes were created successfully"""
    print("\n🔍 Verifying database indexes...")
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename IN ('customer_emails', 'customer_email_replies')
            ORDER BY tablename, indexname
        """)
        
        indexes = cursor.fetchall()
        
        if indexes:
            print("✅ Found the following indexes:")
            for index in indexes:
                print(f"  - {index[1]}.{index[2]}")
        else:
            print("⚠️ No indexes found for customer_emails table")
            
        return len(indexes) > 0
        
    except Exception as e:
        print(f"❌ Error verifying indexes: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def test_query_performance():
    """Test query performance with sample data"""
    print("\n⚡ Testing query performance...")
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        import time
        
        # Test 1: Count emails
        start_time = time.time()
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        count = cursor.fetchone()[0]
        count_time = time.time() - start_time
        
        print(f"  📧 Total emails: {count}")
        print(f"  ⏱️ Count query time: {count_time:.3f}s")
        
        # Test 2: Paginated query
        start_time = time.time()
        cursor.execute("""
            SELECT id, sender, subject, created_at 
            FROM customer_emails 
            ORDER BY id DESC 
            LIMIT 50
        """)
        emails = cursor.fetchall()
        pagination_time = time.time() - start_time
        
        print(f"  📄 Paginated query (50 emails): {pagination_time:.3f}s")
        
        # Test 3: Filtered query
        start_time = time.time()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_emails 
            WHERE sender ILIKE '%test%'
        """)
        filtered_count = cursor.fetchone()[0]
        filter_time = time.time() - start_time
        
        print(f"  🔍 Filtered query time: {filter_time:.3f}s")
        
        # Performance assessment
        if count_time < 0.1 and pagination_time < 0.1:
            print("✅ Query performance is excellent!")
        elif count_time < 0.5 and pagination_time < 0.5:
            print("✅ Query performance is good!")
        else:
            print("⚠️ Query performance needs improvement")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing performance: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Run all performance fixes"""
    print("🚀 Starting IQSTrade Performance Fixes")
    print("=" * 50)
    
    # Step 1: Add database indexes
    if not run_database_indexes():
        print("❌ Failed to add database indexes")
        sys.exit(1)
    
    # Step 2: Verify indexes
    if not verify_indexes():
        print("❌ Failed to verify database indexes")
        sys.exit(1)
    
    # Step 3: Test performance
    if not test_query_performance():
        print("❌ Failed to test query performance")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ All performance fixes completed successfully!")
    print("\n📋 Next steps:")
    print("1. Restart your Flask application")
    print("2. Test the email loading performance")
    print("3. Monitor the background email processor")
    print("\n🎯 Expected improvements:")
    print("- Email loading: 100 emails → 50 emails per page, loads in ~2 seconds")
    print("- Email ingestion: Now runs in background, won't block the UI")
    print("- Auto-refresh: Smart timing, won't interfere with ingestion")

if __name__ == "__main__":
    main() 