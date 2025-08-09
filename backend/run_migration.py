#!/usr/bin/env python3
"""
Run database migration to add CC, BCC, and Reply-To fields
"""

from config import get_db_conn

def run_migration():
    print("🔄 Running database migration: Add CC, BCC, Reply-To fields")
    
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Read and execute migration SQL
        with open('migrations/20250806_add_cc_bcc_fields.sql', 'r') as f:
            migration_sql = f.read()
        
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✅ Migration completed successfully!")
        
        # Verify the changes
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'customer_emails' 
            AND column_name IN ('cc', 'bcc', 'reply_to')
            ORDER BY column_name;
        """)
        
        columns = cursor.fetchall()
        print(f"📋 New columns added: {len(columns)}")
        for col in columns:
            print(f"   - {col[0]}: {col[1]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    run_migration()
