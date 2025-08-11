-- =====================================================
-- FCM Sending Debug Script
-- This will help identify where duplicate FCM notifications are coming from
-- =====================================================

-- 1. CHECK RECENT FCM NOTIFICATIONS BY TYPE
-- =====================================================
SELECT 
    'Recent FCM Notifications by Type:' as info;

SELECT 
    notification_type,
    COUNT(*) as count,
    MIN(sent_at) as first_sent,
    MAX(sent_at) as last_sent
FROM fcm_notifications 
GROUP BY notification_type 
ORDER BY count DESC;

-- 2. CHECK FCM NOTIFICATIONS FOR SPECIFIC EMAILS
-- =====================================================
SELECT 
    'FCM Notifications for Recent Emails:' as info;

SELECT 
    fn.email_id,
    fn.notification_type,
    fn.sent_at,
    ce.subject,
    ce.sender,
    ce.processed_for_payments
FROM fcm_notifications fn
JOIN customer_emails ce ON fn.email_id = ce.id
WHERE ce.created_at > NOW() - INTERVAL '24 hours'
ORDER BY fn.sent_at DESC;

-- 3. CHECK FOR PAYMENT EMAILS WITH MULTIPLE NOTIFICATION TYPES
-- =====================================================
SELECT 
    'Payment Emails with Multiple Notification Types:' as info;

SELECT 
    ce.id,
    ce.subject,
    ce.sender,
    ce.processed_for_payments,
    array_agg(fn.notification_type) as notification_types,
    array_agg(fn.sent_at) as sent_times
FROM customer_emails ce
JOIN fcm_notifications fn ON ce.id = fn.email_id
WHERE ce.processed_for_payments = true
GROUP BY ce.id, ce.subject, ce.sender, ce.processed_for_payments
HAVING COUNT(*) > 1
ORDER BY ce.id DESC;

-- 4. CHECK FCM TOKENS FOR POTENTIAL DUPLICATES
-- =====================================================
SELECT 
    'FCM Tokens Analysis:' as info;

SELECT 
    user_id,
    COUNT(*) as token_count,
    array_agg(token) as tokens,
    array_agg(created_at) as created_times
FROM fcm_tokens
WHERE is_active = true
GROUP BY user_id
HAVING COUNT(*) > 1
ORDER BY token_count DESC;

-- 5. CHECK EMAIL PROCESSING LOCKS
-- =====================================================
SELECT 
    'Email Processing Locks Status:' as info;

SELECT 
    COUNT(*) as total_locks,
    COUNT(CASE WHEN expires_at > NOW() THEN 1 END) as active_locks,
    COUNT(CASE WHEN expires_at <= NOW() THEN 1 END) as expired_locks
FROM email_processing_locks;

-- 6. CHECK RECENT EMAIL PROCESSING ACTIVITY WITH TIMESTAMPS
-- =====================================================
SELECT 
    'Detailed Email Processing Timeline:' as info;

SELECT 
    ce.id,
    ce.subject,
    ce.sender,
    ce.created_at as email_created,
    ce.processed_for_payments,
    fn.notification_type,
    fn.sent_at as notification_sent,
    EXTRACT(EPOCH FROM (fn.sent_at - ce.created_at)) as seconds_between_email_and_notification
FROM customer_emails ce
LEFT JOIN fcm_notifications fn ON ce.id = fn.email_id
WHERE ce.created_at > NOW() - INTERVAL '24 hours'
ORDER BY ce.created_at DESC;

-- 7. CHECK FOR POTENTIAL RACE CONDITIONS
-- =====================================================
SELECT 
    'Potential Race Condition Check:' as info;

SELECT 
    'Emails processed within 1 second of each other:' as description;

SELECT 
    e1.id as email1_id,
    e1.subject as email1_subject,
    e1.created_at as email1_time,
    e2.id as email2_id,
    e2.subject as email2_subject,
    e2.created_at as email2_time,
    EXTRACT(EPOCH FROM (e2.created_at - e1.created_at)) as seconds_difference
FROM customer_emails e1
JOIN customer_emails e2 ON e1.id != e2.id
WHERE e1.created_at > NOW() - INTERVAL '24 hours'
AND e2.created_at > NOW() - INTERVAL '24 hours'
AND ABS(EXTRACT(EPOCH FROM (e2.created_at - e1.created_at))) < 1
ORDER BY e1.created_at DESC;
