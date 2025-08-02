-- Clean up all email-related data to start fresh
-- WARNING: This will delete ALL email data, drafts, and processing locks

-- 1. Clear email processing locks
DELETE FROM email_processing_locks;

-- 2. Clear customer emails (main email table)
DELETE FROM customer_emails;

-- 3. Clear any email-related attachments or files
-- (This depends on your specific table structure)

-- 4. Reset any auto-increment sequences
-- For customer_emails table (adjust table name if different)
SELECT setval(pg_get_serial_sequence('customer_emails', 'id'), 1, false);

-- 5. Clear any email processing status or logs
-- (Add any other email-related tables you have)

-- 6. Verify cleanup
SELECT 'email_processing_locks' as table_name, COUNT(*) as record_count FROM email_processing_locks
UNION ALL
SELECT 'customer_emails' as table_name, COUNT(*) as record_count FROM customer_emails;

-- 7. Optional: Clear FCM tokens if you want to reset notifications too
-- DELETE FROM fcm_tokens;

-- 8. Optional: Reset FCM tokens sequence if you cleared them
-- SELECT setval(pg_get_serial_sequence('fcm_tokens', 'id'), 1, false); 