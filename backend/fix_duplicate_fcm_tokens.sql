-- Fix Duplicate FCM Tokens Script
-- This script helps diagnose and fix duplicate FCM tokens that cause multiple notifications

-- 1. CHECK CURRENT FCM TOKEN STATUS
SELECT 
    'Current FCM Token Status' as info,
    COUNT(*) as total_tokens,
    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_tokens,
    COUNT(DISTINCT user_id) as unique_users
FROM fcm_tokens;

-- 2. SHOW DUPLICATE ACTIVE TOKENS PER USER
SELECT 
    'Duplicate Active Tokens per User' as info,
    user_id,
    COUNT(*) as token_count,
    array_agg(token ORDER BY updated_at DESC) as tokens
FROM fcm_tokens 
WHERE is_active = TRUE 
GROUP BY user_id 
HAVING COUNT(*) > 1
ORDER BY token_count DESC;

-- 3. SHOW ALL ACTIVE TOKENS WITH DETAILS
SELECT 
    'All Active Tokens' as info,
    id,
    user_id,
    token,
    created_at,
    updated_at,
    is_active
FROM fcm_tokens 
WHERE is_active = TRUE 
ORDER BY user_id, updated_at DESC;

-- 4. FIX: DEACTIVATE OLDER DUPLICATE TOKENS (KEEP ONLY THE MOST RECENT PER USER)
-- This will ensure only one active token per user
UPDATE fcm_tokens 
SET is_active = FALSE 
WHERE id IN (
    SELECT id FROM (
        SELECT id,
               ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY updated_at DESC) as rn
        FROM fcm_tokens 
        WHERE is_active = TRUE
    ) ranked 
    WHERE rn > 1
);

-- 5. VERIFY THE FIX
SELECT 
    'After Fix - Active Tokens per User' as info,
    user_id,
    COUNT(*) as token_count
FROM fcm_tokens 
WHERE is_active = TRUE 
GROUP BY user_id 
ORDER BY user_id;

-- 6. SHOW FINAL ACTIVE TOKEN COUNT
SELECT 
    'Final Status' as info,
    COUNT(*) as total_tokens,
    COUNT(CASE WHEN is_active = TRUE THEN 1 END) as active_tokens,
    COUNT(DISTINCT user_id) as unique_users
FROM fcm_tokens;

-- 7. OPTIONAL: SHOW INACTIVE TOKENS (for cleanup reference)
SELECT 
    'Inactive Tokens' as info,
    COUNT(*) as inactive_count,
    COUNT(DISTINCT user_id) as users_with_inactive
FROM fcm_tokens 
WHERE is_active = FALSE;
