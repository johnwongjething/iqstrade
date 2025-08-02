-- Fix fcm_tokens table to allow NULL user_id for public tokens
ALTER TABLE fcm_tokens ALTER COLUMN user_id DROP NOT NULL;

-- Add a comment to explain the change
COMMENT ON COLUMN fcm_tokens.user_id IS 'User ID for authenticated tokens, NULL for public tokens'; 