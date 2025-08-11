-- =====================================================
-- FCM Database Diagnostic and Fix Script
-- Run this in your Railway PostgreSQL database
-- =====================================================

-- 1. CHECK IF FCM_NOTIFICATIONS TABLE EXISTS
-- =====================================================
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'fcm_notifications'
    ) THEN
        RAISE NOTICE '✅ fcm_notifications table EXISTS';
    ELSE
        RAISE NOTICE '❌ fcm_notifications table DOES NOT EXIST - This is why you get duplicate FCM notifications!';
    END IF;
END $$;

-- 2. CHECK ALL TABLES RELATED TO FCM AND NOTIFICATIONS
-- =====================================================
SELECT 
    table_name,
    table_type,
    CASE 
        WHEN table_name LIKE '%fcm%' OR table_name LIKE '%notification%' 
        THEN '🔔 FCM/Notification Related'
        ELSE '📋 Other Tables'
    END as category
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY category DESC, table_name;

-- 3. CHECK FCM_TOKENS TABLE STRUCTURE
-- =====================================================
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'fcm_tokens' 
AND table_schema = 'public'
ORDER BY ordinal_position;

-- 4. CHECK CUSTOMER_EMAILS TABLE STRUCTURE
-- =====================================================
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'customer_emails' 
AND table_schema = 'public'
ORDER BY ordinal_position;

-- 5. IF FCM_NOTIFICATIONS EXISTS, CHECK ITS STRUCTURE
-- =====================================================
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'fcm_notifications' 
AND table_schema = 'public'
ORDER BY ordinal_position;

-- 6. CHECK FOR DUPLICATE FCM NOTIFICATIONS (if table exists)
-- =====================================================
SELECT 
    'Checking for duplicate FCM notifications...' as status;

-- This will only work if the table exists
DO $$
BEGIN
    IF EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'fcm_notifications'
    ) THEN
        -- Check for duplicates
        IF EXISTS (
            SELECT 1 FROM fcm_notifications 
            GROUP BY email_id, notification_type 
            HAVING COUNT(*) > 1
        ) THEN
            RAISE NOTICE '⚠️ DUPLICATE FCM NOTIFICATIONS FOUND!';
        ELSE
            RAISE NOTICE '✅ No duplicate FCM notifications found';
        END IF;
        
        -- Show notification counts
        RAISE NOTICE 'Total FCM notifications: %', (SELECT COUNT(*) FROM fcm_notifications);
        RAISE NOTICE 'Unique email-notification combinations: %', (
            SELECT COUNT(DISTINCT email_id || '-' || notification_type) FROM fcm_notifications
        );
    END IF;
END $$;

-- 7. CHECK RECENT EMAIL PROCESSING ACTIVITY
-- =====================================================
SELECT 
    'Recent email processing activity:' as info;

SELECT 
    id,
    sender,
    subject,
    created_at,
    processed_for_payments,
    message_id
FROM customer_emails 
ORDER BY created_at DESC 
LIMIT 10;

-- 8. CHECK FOR DUPLICATE EMAILS BY MESSAGE_ID
-- =====================================================
SELECT 
    'Checking for duplicate emails by Message-ID:' as info;

SELECT 
    message_id,
    COUNT(*) as duplicate_count,
    array_agg(id) as email_ids,
    array_agg(created_at) as created_times
FROM customer_emails 
WHERE message_id IS NOT NULL 
GROUP BY message_id 
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- 9. CHECK FCM TOKENS STATUS
-- =====================================================
SELECT 
    'FCM Tokens Status:' as info;

SELECT 
    COUNT(*) as total_tokens,
    COUNT(CASE WHEN is_active = true THEN 1 END) as active_tokens,
    COUNT(CASE WHEN is_active = false THEN 1 END) as inactive_tokens
FROM fcm_tokens;

-- 10. CREATE FCM_NOTIFICATIONS TABLE IF IT DOESN'T EXIST
-- =====================================================
CREATE TABLE IF NOT EXISTS fcm_notifications (
    id SERIAL PRIMARY KEY,
    email_id INTEGER REFERENCES customer_emails(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL, -- 'new_email', 'payment_receipt', 'duplicate_payment'
    sent_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add unique constraint to prevent duplicates
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'fcm_notifications_unique_email_type'
    ) THEN
        ALTER TABLE fcm_notifications 
        ADD CONSTRAINT fcm_notifications_unique_email_type 
        UNIQUE (email_id, notification_type);
        RAISE NOTICE '✅ Added unique constraint to prevent duplicate notifications';
    ELSE
        RAISE NOTICE 'ℹ️ Unique constraint already exists';
    END IF;
END $$;

-- Add index for better performance
CREATE INDEX IF NOT EXISTS idx_fcm_notifications_email_type 
ON fcm_notifications(email_id, notification_type);

CREATE INDEX IF NOT EXISTS idx_fcm_notifications_type_sent 
ON fcm_notifications(notification_type, sent_at);

-- 11. FINAL STATUS CHECK
-- =====================================================
SELECT 
    'Final Database Status:' as status;

SELECT 
    'fcm_notifications table exists' as check_item,
    CASE 
        WHEN EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'fcm_notifications'
        ) THEN '✅ YES'
        ELSE '❌ NO'
    END as result

UNION ALL

SELECT 
    'Unique constraint exists' as check_item,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pg_constraint 
            WHERE conname = 'fcm_notifications_unique_email_type'
        ) THEN '✅ YES'
        ELSE '❌ NO'
    END as result

UNION ALL

SELECT 
    'Indexes created' as check_item,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE indexname = 'idx_fcm_notifications_email_type'
        ) THEN '✅ YES'
        ELSE '❌ NO'
    END as result;

-- 12. CLEANUP OPTIONS (UNCOMMENT IF NEEDED)
-- =====================================================
-- WARNING: These will clear all FCM notification history!

-- Option A: Clear all FCM notifications (start fresh)
-- DELETE FROM fcm_notifications;
-- ALTER SEQUENCE fcm_notifications_id_seq RESTART WITH 1;

-- Option B: Clear only duplicate notifications (keep one of each)
-- DELETE FROM fcm_notifications 
-- WHERE id NOT IN (
--     SELECT MIN(id) 
--     FROM fcm_notifications 
--     GROUP BY email_id, notification_type
-- );

-- Option C: Clear notifications older than X days
-- DELETE FROM fcm_notifications 
-- WHERE sent_at < NOW() - INTERVAL '30 days';

-- =====================================================
-- RUN THIS SCRIPT IN YOUR RAILWAY DATABASE
-- =====================================================
