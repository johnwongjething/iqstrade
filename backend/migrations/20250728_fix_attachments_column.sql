-- Fix attachments column to properly handle JSON strings
-- The current TEXT[] array type is causing issues with JSON storage

-- First, let's check the current column type
SELECT 
    column_name,
    data_type,
    udt_name
FROM information_schema.columns 
WHERE table_name = 'customer_emails' 
AND column_name = 'attachments';

-- Convert TEXT[] to JSONB for better JSON handling
ALTER TABLE customer_emails 
ALTER COLUMN attachments TYPE JSONB USING 
    CASE 
        WHEN attachments IS NULL THEN NULL
        WHEN jsonb_typeof(attachments::jsonb) = 'array' THEN attachments::jsonb
        ELSE jsonb_build_array(attachments::text)
    END;

-- Add a comment to document the change
COMMENT ON COLUMN customer_emails.attachments IS 'JSONB array of attachment URLs (Cloudinary links or file paths)';

-- Verify the change
SELECT 
    column_name,
    data_type,
    udt_name
FROM information_schema.columns 
WHERE table_name = 'customer_emails' 
AND column_name = 'attachments'; 