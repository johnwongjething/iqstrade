#!/usr/bin/env python3
"""
Comprehensive Database Schema Analysis
Provides a complete picture of your database structure
"""
import os
import sys
from config import get_db_conn

def analyze_database_schema():
    """Analyze the complete database schema"""
    print("🔍 Comprehensive Database Schema Analysis")
    print("=" * 80)
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Found {len(tables)} tables in database:")
        print("-" * 80)
        
        for table in tables:
            print(f"  📊 {table}")
        
        print("\n" + "=" * 80)
        
        # Analyze each table in detail
        for table in tables:
            analyze_table(cursor, table)
            print("-" * 80)
        
        # Get table relationships
        print("\n🔗 Table Relationships:")
        print("-" * 80)
        analyze_relationships(cursor, tables)
        
        # Get indexes
        print("\n📈 Indexes:")
        print("-" * 80)
        analyze_indexes(cursor, tables)
        
        # Get constraints
        print("\n🔒 Constraints:")
        print("-" * 80)
        analyze_constraints(cursor, tables)
        
        # Get sample data counts
        print("\n📊 Sample Data Counts:")
        print("-" * 80)
        analyze_data_counts(cursor, tables)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema analysis failed: {e}")
        return False

def analyze_table(cursor, table_name):
    """Analyze a specific table"""
    print(f"\n📋 Table: {table_name}")
    
    # Get columns
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            udt_name,
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
    print(f"  Columns ({len(columns)}):")
    
    for col in columns:
        column_name, data_type, udt_name, is_nullable, column_default, char_max_len, num_precision, num_scale = col
        
        # Format the column info
        nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
        default = f" DEFAULT {column_default}" if column_default else ""
        
        # Add length/precision info
        type_info = data_type
        if char_max_len:
            type_info += f"({char_max_len})"
        elif num_precision:
            if num_scale:
                type_info += f"({num_precision},{num_scale})"
            else:
                type_info += f"({num_precision})"
        
        print(f"    {column_name:<25} {type_info:<20} {nullable:<10}{default}")
    
    # Get primary key
    cursor.execute("""
        SELECT column_name
        FROM information_schema.key_column_usage
        WHERE table_name = %s AND constraint_name IN (
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = %s AND constraint_type = 'PRIMARY KEY'
        )
    """, (table_name, table_name))
    
    pk_columns = [row[0] for row in cursor.fetchall()]
    if pk_columns:
        print(f"  Primary Key: {', '.join(pk_columns)}")
    
    # Get foreign keys
    cursor.execute("""
        SELECT 
            column_name,
            referenced_table_name,
            referenced_column_name
        FROM information_schema.key_column_usage
        WHERE table_name = %s AND referenced_table_name IS NOT NULL
    """, (table_name,))
    
    fk_columns = cursor.fetchall()
    if fk_columns:
        print(f"  Foreign Keys:")
        for fk in fk_columns:
            column_name, ref_table, ref_column = fk
            print(f"    {column_name} -> {ref_table}.{ref_column}")

def analyze_relationships(cursor, tables):
    """Analyze table relationships"""
    for table in tables:
        cursor.execute("""
            SELECT 
                column_name,
                referenced_table_name,
                referenced_column_name
            FROM information_schema.key_column_usage
            WHERE table_name = %s AND referenced_table_name IS NOT NULL
        """, (table,))
        
        fks = cursor.fetchall()
        if fks:
            print(f"  {table}:")
            for fk in fks:
                column_name, ref_table, ref_column = fk
                print(f"    {column_name} -> {ref_table}.{ref_column}")

def analyze_indexes(cursor, tables):
    """Analyze indexes"""
    for table in tables:
        cursor.execute("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes 
            WHERE tablename = %s
            ORDER BY indexname
        """, (table,))
        
        indexes = cursor.fetchall()
        if indexes:
            print(f"  {table}:")
            for index in indexes:
                index_name, index_def = index
                print(f"    {index_name}: {index_def}")

def analyze_constraints(cursor, tables):
    """Analyze constraints"""
    for table in tables:
        cursor.execute("""
            SELECT 
                constraint_name,
                constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = %s
            ORDER BY constraint_type, constraint_name
        """, (table,))
        
        constraints = cursor.fetchall()
        if constraints:
            print(f"  {table}:")
            for constraint in constraints:
                constraint_name, constraint_type = constraint
                print(f"    {constraint_type}: {constraint_name}")

def analyze_data_counts(cursor, tables):
    """Get row counts for each table"""
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count:,} rows")
        except Exception as e:
            print(f"  {table}: Error getting count - {e}")

def generate_schema_summary():
    """Generate a summary of the schema"""
    print("\n📋 Schema Summary:")
    print("=" * 80)
    
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Get all tables with their purposes
        table_purposes = {
            'users': 'User authentication and management',
            'bill_of_lading': 'Core shipping documents with OCR processing',
            'password_reset_tokens': 'Password reset functionality',
            'audit_logs': 'System activity tracking',
            'customer_emails': 'AI-processed email management',
            'customer_email_replies': 'AI-generated email replies',
            'bank_unmatched_records': 'Payment reconciliation',
            'unmatched_receipts': 'Payment receipt tracking'
        }
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        print("📊 Core Tables:")
        for table in tables:
            purpose = table_purposes.get(table, 'Custom table')
            print(f"  • {table}: {purpose}")
        
        # Get key metrics
        print(f"\n📈 Key Metrics:")
        
        # User count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"  • Total Users: {user_count}")
        
        # Bill of lading count
        cursor.execute("SELECT COUNT(*) FROM bill_of_lading")
        bl_count = cursor.fetchone()[0]
        print(f"  • Total Bills of Lading: {bl_count}")
        
        # Email count
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        email_count = cursor.fetchone()[0]
        print(f"  • Total Customer Emails: {email_count}")
        
        # Emails with attachments
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_emails 
            WHERE attachments IS NOT NULL AND attachments != '[]' AND attachments != 'null'
        """)
        email_with_attachments = cursor.fetchone()[0]
        print(f"  • Emails with Attachments: {email_with_attachments}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Summary generation failed: {e}")

def export_schema_to_file():
    """Export schema to a file for reference"""
    print("\n💾 Exporting schema to file...")
    
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Get all table creation scripts
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        with open('database_schema_export.sql', 'w') as f:
            f.write("-- Database Schema Export\n")
            f.write("-- Generated by analyze_db_schema.py\n")
            f.write("-- Date: " + str(conn.cursor().execute("SELECT NOW()").fetchone()[0]) + "\n\n")
            
            for table in tables:
                # Get table structure
                cursor.execute(f"SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position")
                columns = cursor.fetchall()
                
                f.write(f"-- Table: {table}\n")
                f.write(f"CREATE TABLE IF NOT EXISTS {table} (\n")
                
                column_defs = []
                for col in columns:
                    column_name, data_type, is_nullable, column_default = col
                    nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                    default = f" DEFAULT {column_default}" if column_default else ""
                    column_defs.append(f"    {column_name} {data_type} {nullable}{default}")
                
                f.write(",\n".join(column_defs))
                f.write("\n);\n\n")
        
        print("✅ Schema exported to: database_schema_export.sql")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Export failed: {e}")

def main():
    """Main function"""
    print("🚀 Database Schema Analysis")
    print("=" * 80)
    
    # Analyze schema
    if not analyze_database_schema():
        return
    
    # Generate summary
    generate_schema_summary()
    
    # Export schema
    export_schema_to_file()
    
    print("\n✅ Schema analysis completed!")
    print("\n💡 Next steps:")
    print("  1. Review the schema above")
    print("  2. Check database_schema_export.sql for reference")
    print("  3. Plan your new features based on existing structure")

if __name__ == "__main__":
    main() 