#!/usr/bin/env python3
from config import get_db_conn

def run_migration():
    """Run the migration to add 'to' field to customer_emails table"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Read the migration SQL file
        with open('migrations/20250809_add_to_field.sql', 'r') as f:
            migration_sql = f.read()
        
        print("Running migration: 20250809_add_to_field.sql")
        print("=" * 50)
        
        # Execute the migration
        cursor.execute(migration_sql)
        
        # Commit the changes
        conn.commit()
        
        print("✅ Migration completed successfully!")
        print("✅ Added 'to' field to customer_emails table")
        print("✅ Created GIN index for performance")
        print("✅ Added documentation comments")
        
        # Verify the changes
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'customer_emails' 
            AND column_name = 'to'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"✅ Verification: 'to' column exists - {result[0]} ({result[1]}, nullable: {result[2]})")
        else:
            print("❌ Verification failed: 'to' column not found")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    run_migration()
