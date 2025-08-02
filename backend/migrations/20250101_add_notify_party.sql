-- Migration to add notify_party field to bill_of_lading table
-- Date: 2025-01-01

-- Add notify_party column to bill_of_lading table
ALTER TABLE bill_of_lading 
ADD COLUMN IF NOT EXISTS notify_party TEXT;

-- Add comment for documentation
COMMENT ON COLUMN bill_of_lading.notify_party IS 'Notify party information from BOL/AWB documents';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_notify_party ON bill_of_lading(notify_party);

-- Update existing records to extract notify_party from consignee field if it contains multiple parties
-- This is a data cleanup step for existing records that have mixed consignee/notify party data
-- We'll use a more generic approach to identify potential notify party information

-- Pattern 1: Look for records with multiple company names separated by common delimiters
UPDATE bill_of_lading 
SET notify_party = CASE 
    WHEN consignee LIKE '%\n%' THEN 
        SPLIT_PART(consignee, '\n', 2)
    WHEN consignee LIKE '%;%' THEN 
        SPLIT_PART(consignee, ';', 2)
    WHEN consignee LIKE '%|%' THEN 
        SPLIT_PART(consignee, '|', 2)
    WHEN consignee LIKE '% - %' THEN 
        SPLIT_PART(consignee, ' - ', 2)
    WHEN consignee LIKE '% / %' THEN 
        SPLIT_PART(consignee, ' / ', 2)
    ELSE NULL 
END
WHERE notify_party IS NULL 
AND (
    consignee LIKE '%\n%' OR 
    consignee LIKE '%;%' OR 
    consignee LIKE '%|%' OR 
    consignee LIKE '% - %' OR 
    consignee LIKE '% / %'
);

-- Pattern 2: Look for records with multiple phone numbers (indicates multiple parties)
UPDATE bill_of_lading 
SET notify_party = CASE 
    WHEN (LENGTH(consignee) - LENGTH(REPLACE(consignee, 'TEL:', ''))) / 4 > 1 THEN
        SUBSTRING(consignee FROM POSITION('TEL:' IN SUBSTRING(consignee FROM POSITION('TEL:' IN consignee) + 4)))
    ELSE NULL 
END
WHERE notify_party IS NULL 
AND (LENGTH(consignee) - LENGTH(REPLACE(consignee, 'TEL:', ''))) / 4 > 1;

-- Clean up consignee field to remove the extracted notify party information
UPDATE bill_of_lading 
SET consignee = CASE 
    WHEN notify_party IS NOT NULL AND consignee LIKE '%\n%' THEN 
        SPLIT_PART(consignee, '\n', 1)
    WHEN notify_party IS NOT NULL AND consignee LIKE '%;%' THEN 
        SPLIT_PART(consignee, ';', 1)
    WHEN notify_party IS NOT NULL AND consignee LIKE '%|%' THEN 
        SPLIT_PART(consignee, '|', 1)
    WHEN notify_party IS NOT NULL AND consignee LIKE '% - %' THEN 
        SPLIT_PART(consignee, ' - ', 1)
    WHEN notify_party IS NOT NULL AND consignee LIKE '% / %' THEN 
        SPLIT_PART(consignee, ' / ', 1)
    WHEN notify_party IS NOT NULL AND (LENGTH(consignee) - LENGTH(REPLACE(consignee, 'TEL:', ''))) / 4 > 1 THEN
        SPLIT_PART(consignee, 'TEL:', 1)
    ELSE consignee 
END
WHERE notify_party IS NOT NULL; 