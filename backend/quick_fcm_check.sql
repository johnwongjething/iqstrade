-- =====================================================
-- QUICK FCM Database Check - Essential Only
-- Run this first to see the basic status
-- =====================================================

-- 1. Check if fcm_notifications table exists
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'fcm_notifications'
        ) THEN '✅ EXISTS'
        ELSE '❌ MISSING - This causes duplicate FCM notifications!'
    END as fcm_notifications_table_status;

-- 2. If table exists, check for duplicates
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
        
        -- Show counts
        RAISE NOTICE 'Total notifications: %', (SELECT COUNT(*) FROM fcm_notifications);
    ELSE
        RAISE NOTICE '❌ fcm_notifications table does not exist';
    END IF;
END $$;

-- 3. Check recent email activity
SELECT 
    'Recent emails (last 5):' as info;

SELECT 
    id,
    sender,
    subject,
    created_at,
    processed_for_payments
FROM customer_emails 
ORDER BY created_at DESC 
LIMIT 5;

-- 4. Check for duplicate emails
SELECT 
    'Duplicate emails by Message-ID:' as info;

SELECT 
    message_id,
    COUNT(*) as count
FROM customer_emails 
WHERE message_id IS NOT NULL 
GROUP BY message_id 
HAVING COUNT(*) > 1
ORDER BY count DESC
LIMIT 5;
