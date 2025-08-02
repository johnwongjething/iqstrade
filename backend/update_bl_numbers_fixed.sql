-- PostgreSQL script to update existing emails with BL numbers (FIXED VERSION)
-- Run this script while logged into PostgreSQL

-- Function to extract BL numbers from text
CREATE OR REPLACE FUNCTION extract_bl_numbers(text_content TEXT)
RETURNS TEXT[] AS $$
DECLARE
    bl_numbers TEXT[] := '{}';
    bl_patterns TEXT[] := ARRAY[
        'BL[-\s]?(\d{6,})',           -- BL followed by 6+ digits
        '(\d{6,})[-\s]?BL',           -- 6+ digits followed by BL
        'Bill\s+of\s+Lading[:\s]*(\d{6,})', -- Bill of Lading followed by numbers
        '(\d{6,})\s*[-.]?\s*NYC',     -- Numbers followed by NYC
        'NYC(\d{3,})',                -- NYC followed by 3+ digits
        '(\d{3,})[-.]?\s*NYC',        -- 3+ digits followed by NYC
        'BL\s*(\d{3,}[-.]?\d{3,})'    -- BL with format like 001-123
    ];
    pattern TEXT;
    matches TEXT[];
    match TEXT;
    bl TEXT;
BEGIN
    -- Loop through each pattern
    FOREACH pattern IN ARRAY bl_patterns
    LOOP
        -- Find all matches for this pattern
        SELECT array_agg(match) INTO matches
        FROM regexp_matches(text_content, pattern, 'gi') AS match;
        
        -- Add each match to bl_numbers if it's not already there
        IF matches IS NOT NULL THEN
            FOREACH match IN ARRAY matches
            LOOP
                bl := trim(match);
                IF length(bl) >= 3 AND NOT (bl = ANY(bl_numbers)) THEN
                    bl_numbers := array_append(bl_numbers, bl);
                END IF;
            END LOOP;
        END IF;
    END LOOP;
    
    RETURN bl_numbers;
END;
$$ LANGUAGE plpgsql;

-- Update emails with extracted BL numbers (FIXED VERSION)
DO $$
DECLARE
    email_record RECORD;
    extracted_bl_numbers TEXT[];
    updated_count INTEGER := 0;
BEGIN
    -- Get all emails that don't have BL numbers (FIXED: use table alias)
    FOR email_record IN 
        SELECT e.id, e.sender, e.subject, e.body, e.bl_numbers 
        FROM customer_emails e
        WHERE e.bl_numbers IS NULL OR array_length(e.bl_numbers, 1) IS NULL
        ORDER BY e.created_at DESC
    LOOP
        -- Extract BL numbers from subject and body
        extracted_bl_numbers := extract_bl_numbers(
            COALESCE(email_record.subject, '') || ' ' || COALESCE(email_record.body, '')
        );
        
        -- Update the email with extracted BL numbers
        UPDATE customer_emails 
        SET bl_numbers = extracted_bl_numbers 
        WHERE id = email_record.id;
        
        updated_count := updated_count + 1;
        
        -- Print progress (optional)
        IF array_length(extracted_bl_numbers, 1) > 0 THEN
            RAISE NOTICE 'Updated email %: BL numbers = %', email_record.id, extracted_bl_numbers;
        ELSE
            RAISE NOTICE 'Email %: No BL numbers found', email_record.id;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Successfully updated % emails with BL numbers', updated_count;
    
    -- Show final statistics
    RAISE NOTICE 'Total emails with BL numbers: %', 
        (SELECT COUNT(*) FROM customer_emails WHERE bl_numbers IS NOT NULL AND array_length(bl_numbers, 1) > 0);
END $$;

-- Clean up the function
DROP FUNCTION extract_bl_numbers(TEXT);

-- Show final results
SELECT 
    COUNT(*) as total_emails,
    COUNT(CASE WHEN bl_numbers IS NOT NULL AND array_length(bl_numbers, 1) > 0 THEN 1 END) as emails_with_bl,
    COUNT(CASE WHEN bl_numbers IS NULL OR array_length(bl_numbers, 1) IS NULL THEN 1 END) as emails_without_bl
FROM customer_emails;

-- Show some examples of emails with BL numbers
SELECT id, sender, subject, bl_numbers 
FROM customer_emails 
WHERE bl_numbers IS NOT NULL AND array_length(bl_numbers, 1) > 0
ORDER BY created_at DESC 
LIMIT 10; 