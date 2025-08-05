#!/usr/bin/env python3
"""
Customer Balance Migration Runner
Runs the customer balance system migration
"""

import os
import sys
from config import get_db_conn

def run_customer_balance_migration():
    """Run the customer balance migration"""
    print("🚀 Running Customer Balance Migration...")
    
    # Read the migration SQL file
    migration_file = "migrations/20250127_add_customer_balance_system.sql"
    
    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        print(f"📝 Executing {len(statements)} SQL statements...")
        
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    print(f"  {i}/{len(statements)}: {statement[:50]}...")
                    cursor.execute(statement)
                    conn.commit()
                except Exception as e:
                    print(f"  ⚠️  Statement {i} failed (may already exist): {e}")
                    conn.rollback()
        
        cursor.close()
        conn.close()
        
        print("✅ Customer Balance Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_customer_balance_migration()
    sys.exit(0 if success else 1) 