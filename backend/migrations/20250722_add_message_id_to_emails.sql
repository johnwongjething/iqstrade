-- Add message_id to customer_emails to prevent duplicates
ALTER TABLE customer_emails ADD COLUMN message_id VARCHAR(255) UNIQUE; 