-- SQL script to fix email status issues
-- This script will help identify and fix emails that incorrectly show as "Sent"

-- 1. First, let's see what's in the customer_email_replies table
SELECT 
    'Current reply data' as info,
    COUNT(*) as total_replies,
    COUNT(CASE WHEN is_draft = FALSE THEN 1 END) as sent_replies,
    COUNT(CASE WHEN is_draft = TRUE THEN 1 END) as draft_replies
FROM customer_email_replies;

-- 2. Show emails that have sent replies (these will show as "Sent")
SELECT 
    e.id as email_id,
    e.subject,
    e.created_at as email_created,
    COUNT(r.id) as total_replies,
    COUNT(CASE WHEN r.is_draft = FALSE THEN 1 END) as sent_replies,
    COUNT(CASE WHEN r.is_draft = TRUE THEN 1 END) as draft_replies
FROM customer_emails e
LEFT JOIN customer_email_replies r ON e.id = r.customer_email_id
GROUP BY e.id, e.subject, e.created_at
HAVING COUNT(CASE WHEN r.is_draft = FALSE THEN 1 END) > 0
ORDER BY e.created_at DESC
LIMIT 10;

-- 3. Show the actual sent replies that are causing the issue
SELECT 
    r.id as reply_id,
    r.customer_email_id as email_id,
    e.subject as email_subject,
    r.content as reply_content,
    r.is_draft,
    r.created_at as reply_created
FROM customer_email_replies r
JOIN customer_emails e ON r.customer_email_id = e.id
WHERE r.is_draft = FALSE
ORDER BY r.created_at DESC
LIMIT 10;

-- 4. If you want to fix the issue by marking all replies as drafts (temporary fix)
-- Uncomment the following lines if you want to apply this fix:
/*
UPDATE customer_email_replies 
SET is_draft = TRUE 
WHERE is_draft = FALSE;

-- Verify the fix
SELECT 
    'After fix' as info,
    COUNT(*) as total_replies,
    COUNT(CASE WHEN is_draft = FALSE THEN 1 END) as sent_replies,
    COUNT(CASE WHEN is_draft = TRUE THEN 1 END) as draft_replies
FROM customer_email_replies;
*/ 