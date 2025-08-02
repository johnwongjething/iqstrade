-- Migration to add container breakdown columns
-- Date: 2025-01-01

-- Add container breakdown columns
ALTER TABLE bill_of_lading 
ADD COLUMN IF NOT EXISTS container_count_20ft INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS container_count_40ft INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS container_count_40ft_hc INTEGER DEFAULT 0;

-- Add comments for documentation
COMMENT ON COLUMN bill_of_lading.container_count_20ft IS 'Number of 20ft containers';
COMMENT ON COLUMN bill_of_lading.container_count_40ft IS 'Number of 40ft containers';
COMMENT ON COLUMN bill_of_lading.container_count_40ft_hc IS 'Number of 40ft high cube containers';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_container_20ft ON bill_of_lading(container_count_20ft);
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_container_40ft ON bill_of_lading(container_count_40ft);
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_container_40ft_hc ON bill_of_lading(container_count_40ft_hc); 