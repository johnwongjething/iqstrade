#!/usr/bin/env python3
"""
Detailed Database Schema Analysis
Comprehensive analysis of your database structure for future additions
"""

import os
import sys
from datetime import datetime
from config import get_db_conn

def analyze_database_schema():
    """Comprehensive database schema analysis"""
    
    print("🗄️ DETAILED DATABASE SCHEMA ANALYSIS")
    print("=" * 60)
    print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        db_conn = get_db_conn()
        cursor = db_conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Total Tables Found: {len(tables)}")
        print(f"📋 Tables: {', '.join(tables)}")
        print("\n" + "=" * 60)
        
        # Analyze each table in detail
        for table_name in tables:
            analyze_table(cursor, table_name)
            print("\n" + "-" * 60)
        
        # Generate summary
        generate_schema_summary(cursor, tables)
        
        # Generate SQL for future additions
        generate_future_additions_template(cursor, tables)
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")
        import traceback
        traceback.print_exc()

def analyze_table(cursor, table_name):
    """Analyze a single table in detail"""
    
    print(f"📋 TABLE: {table_name.upper()}")
    print("=" * 40)
    
    # Get column information
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position
    """, (table_name,))
    
    columns = cursor.fetchall()
    
    print(f"📊 Columns ({len(columns)}):")
    print(f"{'Column Name':<25} {'Type':<20} {'Nullable':<8} {'Default':<15} {'Length/Precision':<15}")
    print("-" * 85)
    
    for col in columns:
        col_name, data_type, nullable, default, max_length, precision, scale = col
        
        # Format type with length/precision
        type_info = data_type
        if max_length:
            type_info += f"({max_length})"
        elif precision:
            if scale:
                type_info += f"({precision},{scale})"
            else:
                type_info += f"({precision})"
        
        # Format default
        default_str = str(default) if default else "NULL"
        if len(default_str) > 14:
            default_str = default_str[:11] + "..."
        
        print(f"{col_name:<25} {type_info:<20} {nullable:<8} {default_str:<15} {str(max_length or precision or ''):<15}")
    
    # Get constraints
    cursor.execute("""
        SELECT 
            constraint_name,
            constraint_type,
            column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu 
            ON tc.constraint_name = ccu.constraint_name
        WHERE tc.table_name = %s
        ORDER BY constraint_type, constraint_name
    """, (table_name,))
    
    constraints = cursor.fetchall()
    
    if constraints:
        print(f"\n🔒 Constraints:")
        for constraint_name, constraint_type, column_name in constraints:
            print(f"   {constraint_type.upper()}: {constraint_name} ({column_name})")
    
    # Get indexes
    cursor.execute("""
        SELECT 
            indexname,
            indexdef
        FROM pg_indexes 
        WHERE tablename = %s
        ORDER BY indexname
    """, (table_name,))
    
    indexes = cursor.fetchall()
    
    if indexes:
        print(f"\n📈 Indexes:")
        for index_name, index_def in indexes:
            print(f"   {index_name}: {index_def}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    print(f"\n📊 Row Count: {row_count:,}")
    
    # Get sample data (first 3 rows)
    if row_count > 0:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        sample_rows = cursor.fetchall()
        
        if sample_rows:
            print(f"\n📋 Sample Data (first 3 rows):")
            for i, row in enumerate(sample_rows, 1):
                print(f"   Row {i}: {row}")
    
    # Get foreign keys
    cursor.execute("""
        SELECT 
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = %s
    """, (table_name,))
    
    foreign_keys = cursor.fetchall()
    
    if foreign_keys:
        print(f"\n🔗 Foreign Keys:")
        for fk_col, fk_table, fk_column in foreign_keys:
            print(f"   {fk_col} → {fk_table}.{fk_column}")

def generate_schema_summary(cursor, tables):
    """Generate a summary of the entire schema"""
    
    print("\n📊 SCHEMA SUMMARY")
    print("=" * 60)
    
    total_tables = len(tables)
    total_columns = 0
    total_rows = 0
    
    for table_name in tables:
        # Count columns
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = %s
        """, (table_name,))
        column_count = cursor.fetchone()[0]
        total_columns += column_count
        
        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        total_rows += row_count
    
    print(f"📋 Total Tables: {total_tables}")
    print(f"📊 Total Columns: {total_columns}")
    print(f"📈 Total Rows: {total_rows:,}")
    
    # Table sizes
    print(f"\n📏 Table Sizes:")
    for table_name in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"   {table_name}: {row_count:,} rows")

def generate_future_additions_template(cursor, tables):
    """Generate template for future additions"""
    
    print("\n🔮 FUTURE ADDITIONS TEMPLATE")
    print("=" * 60)
    
    print("📝 SQL Template for New Tables:")
    print("""
-- Example: Adding a new table
CREATE TABLE new_table_name (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Add your columns here
    column_name DATA_TYPE [CONSTRAINTS],
    -- Foreign keys
    foreign_key_id INTEGER REFERENCES existing_table(id),
    -- Indexes for performance
    CONSTRAINT idx_new_table_column_name UNIQUE (column_name)
);

-- Add indexes for performance
CREATE INDEX idx_new_table_created_at ON new_table_name(created_at);
CREATE INDEX idx_new_table_foreign_key ON new_table_name(foreign_key_id);

-- Add comments for documentation
COMMENT ON TABLE new_table_name IS 'Description of the table';
COMMENT ON COLUMN new_table_name.column_name IS 'Description of the column';
""")
    
    print("\n📋 Common Data Types in Your Schema:")
    cursor.execute("""
        SELECT DISTINCT data_type, COUNT(*) as count
        FROM information_schema.columns 
        WHERE table_schema = 'public'
        GROUP BY data_type
        ORDER BY count DESC
    """)
    
    data_types = cursor.fetchall()
    for data_type, count in data_types:
        print(f"   {data_type}: {count} columns")
    
    print("\n🔗 Common Foreign Key Patterns:")
    print("   - id INTEGER REFERENCES table_name(id)")
    print("   - user_id INTEGER REFERENCES users(id)")
    print("   - email_id INTEGER REFERENCES customer_emails(id)")
    print("   - created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
    print("   - updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()")

def export_schema_to_file():
    """Export schema to a file for reference"""
    
    schema_file = f"database_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    
    print(f"\n💾 Exporting schema to: {schema_file}")
    
    # Redirect output to file
    import sys
    original_stdout = sys.stdout
    
    with open(schema_file, 'w', encoding='utf-8') as f:
        sys.stdout = f
        analyze_database_schema()
        sys.stdout = original_stdout
    
    print(f"✅ Schema exported to: {schema_file}")

if __name__ == "__main__":
    print("🗄️ Starting detailed database schema analysis...")
    analyze_database_schema()
    
    # Ask if user wants to export
    response = input("\n💾 Export schema to file? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        export_schema_to_file()
    
    print("\n🎉 Schema analysis complete!") 