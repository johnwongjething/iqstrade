-- Complete Database Schema Extraction Script
-- Run this in your Railway PostgreSQL database to get full schema information
-- Copy the output and share it with me for verification

-- ========================================
-- 1. TABLE OVERVIEW
-- ========================================
SELECT 
    '=== TABLE OVERVIEW ===' as section;

SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count,
    (SELECT COUNT(*) FROM pg_indexes WHERE tablename = t.table_name) as index_count
FROM information_schema.tables t
WHERE table_schema = 'public'
ORDER BY table_name;

-- ========================================
-- 2. DETAILED TABLE SCHEMAS
-- ========================================
SELECT 
    '=== DETAILED TABLE SCHEMAS ===' as section;

SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length,
    numeric_precision,
    numeric_scale,
    ordinal_position
FROM information_schema.columns 
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- ========================================
-- 3. PRIMARY KEYS
-- ========================================
SELECT 
    '=== PRIMARY KEYS ===' as section;

SELECT 
    tc.table_name,
    kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'PRIMARY KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name;

-- ========================================
-- 4. FOREIGN KEYS
-- ========================================
SELECT 
    '=== FOREIGN KEYS ===' as section;

SELECT 
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;

-- ========================================
-- 5. INDEXES
-- ========================================
SELECT 
    '=== INDEXES ===' as section;

SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- ========================================
-- 6. CONSTRAINTS
-- ========================================
SELECT 
    '=== CONSTRAINTS ===' as section;

SELECT 
    table_name,
    constraint_name,
    constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'public'
ORDER BY table_name, constraint_type;

-- ========================================
-- 7. TABLE ROW COUNTS
-- ========================================
SELECT 
    '=== TABLE ROW COUNTS ===' as section;

SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count,
    n_tup_ins as total_inserts,
    n_tup_upd as total_updates,
    n_tup_del as total_deletes
FROM pg_stat_user_tables
ORDER BY tablename;

-- ========================================
-- 8. DATA TYPES SUMMARY
-- ========================================
SELECT 
    '=== DATA TYPES SUMMARY ===' as section;

SELECT 
    data_type,
    COUNT(*) as usage_count
FROM information_schema.columns 
WHERE table_schema = 'public'
GROUP BY data_type
ORDER BY usage_count DESC;

-- ========================================
-- 9. COLUMN NAMES BY PATTERN
-- ========================================
SELECT 
    '=== COLUMN NAMES BY PATTERN ===' as section;

-- Timestamp columns
SELECT 
    'TIMESTAMP COLUMNS' as pattern,
    table_name,
    column_name,
    data_type
FROM information_schema.columns 
WHERE table_schema = 'public'
    AND (column_name LIKE '%_at' OR column_name = 'timestamp')
ORDER BY table_name, column_name;

-- ID columns
SELECT 
    'ID COLUMNS' as pattern,
    table_name,
    column_name,
    data_type
FROM information_schema.columns 
WHERE table_schema = 'public'
    AND column_name LIKE '%id%'
ORDER BY table_name, column_name;

-- ========================================
-- 10. SPECIFIC TABLE VERIFICATION
-- ========================================
SELECT 
    '=== SPECIFIC TABLE VERIFICATION ===' as section;

-- Check if audit_logs table exists and has correct structure
SELECT 
    'AUDIT_LOGS TABLE CHECK' as check_name,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') 
        THEN 'EXISTS' 
        ELSE 'MISSING' 
    END as table_status,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'audit_logs') as column_count,
    (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'audit_logs') as index_count;

-- Check if all required tables exist
SELECT 
    'REQUIRED TABLES CHECK' as check_name,
    table_name,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = t.table_name) 
        THEN 'EXISTS' 
        ELSE 'MISSING' 
    END as status
FROM (VALUES 
    ('users'),
    ('bill_of_lading'),
    ('customer_emails'),
    ('customer_email_replies'),
    ('password_reset_tokens'),
    ('audit_logs')
) AS t(table_name)
ORDER BY table_name;

-- ========================================
-- 11. PERFORMANCE INDEXES VERIFICATION
-- ========================================
SELECT 
    '=== PERFORMANCE INDEXES VERIFICATION ===' as section;

-- Check for performance indexes
SELECT 
    'PERFORMANCE INDEXES' as check_name,
    tablename,
    indexname,
    CASE 
        WHEN indexname LIKE 'idx_%' THEN 'PERFORMANCE INDEX'
        ELSE 'OTHER INDEX'
    END as index_type
FROM pg_indexes 
WHERE schemaname = 'public'
    AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- ========================================
-- 12. DATABASE VERSION AND SETTINGS
-- ========================================
SELECT 
    '=== DATABASE VERSION AND SETTINGS ===' as section;

SELECT 
    'DATABASE VERSION' as setting_name,
    version() as value;

SELECT 
    'CURRENT DATABASE' as setting_name,
    current_database() as value;

SELECT 
    'CURRENT SCHEMA' as setting_name,
    current_schema as value;

-- ========================================
-- 13. SUMMARY REPORT
-- ========================================
SELECT 
    '=== SUMMARY REPORT ===' as section;

SELECT 
    'TOTAL TABLES' as metric,
    COUNT(*) as value
FROM information_schema.tables 
WHERE table_schema = 'public';

SELECT 
    'TOTAL INDEXES' as metric,
    COUNT(*) as value
FROM pg_indexes 
WHERE schemaname = 'public';

SELECT 
    'TOTAL FOREIGN KEYS' as metric,
    COUNT(*) as value
FROM information_schema.table_constraints 
WHERE table_schema = 'public' 
    AND constraint_type = 'FOREIGN KEY';

SELECT 
    'PERFORMANCE INDEXES' as metric,
    COUNT(*) as value
FROM pg_indexes 
WHERE schemaname = 'public' 
    AND indexname LIKE 'idx_%';

-- ========================================
-- END OF SCHEMA EXTRACTION
-- ========================================
SELECT 
    '=== SCHEMA EXTRACTION COMPLETE ===' as section,
    'Copy all output above and share it for verification' as instruction; 