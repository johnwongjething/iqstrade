-- Enhanced Pricing Schema Migration
-- Add new columns to bill_of_lading table for proper fee calculation

-- Add shipment type and container details
ALTER TABLE bill_of_lading 
ADD COLUMN IF NOT EXISTS shipment_type VARCHAR(20) DEFAULT 'ocean', -- 'ocean', 'air', 'loose_cargo'
ADD COLUMN IF NOT EXISTS container_type VARCHAR(20), -- '20ft', '40ft', '40ft_hc', 'loose_cargo'
ADD COLUMN IF NOT EXISTS container_count INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS total_weight_kg DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS weight_unit VARCHAR(10) DEFAULT 'kg', -- 'kg', 'lbs'

-- Add pricing configuration
ADD COLUMN IF NOT EXISTS pricing_method VARCHAR(20) DEFAULT 'container', -- 'container', 'weight', 'mixed'
ADD COLUMN IF NOT EXISTS base_ctn_fee DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS base_service_fee DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS calculated_ctn_fee DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS calculated_service_fee DECIMAL(10,2),

-- Add OCR confidence and manual override flags
ADD COLUMN IF NOT EXISTS ocr_confidence_score DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS manual_override BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS override_reason TEXT,
ADD COLUMN IF NOT EXISTS override_by VARCHAR(100),
ADD COLUMN IF NOT EXISTS override_at TIMESTAMPTZ,

-- Add audit fields
ADD COLUMN IF NOT EXISTS pricing_calculation_log JSONB,
ADD COLUMN IF NOT EXISTS last_pricing_update TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

-- Create pricing configuration table
CREATE TABLE IF NOT EXISTS pricing_config (
    id SERIAL PRIMARY KEY,
    shipment_type VARCHAR(20) NOT NULL,
    container_type VARCHAR(20),
    pricing_method VARCHAR(20) NOT NULL,
    ctn_fee_per_unit DECIMAL(10,2) NOT NULL,
    service_fee_per_unit DECIMAL(10,2) NOT NULL,
    unit_type VARCHAR(20) NOT NULL, -- 'container', 'kg', 'lbs'
    minimum_charge DECIMAL(10,2) DEFAULT 0,
    maximum_charge DECIMAL(10,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    notes TEXT
);

-- Insert default pricing configurations
INSERT INTO pricing_config (shipment_type, container_type, pricing_method, ctn_fee_per_unit, service_fee_per_unit, unit_type, minimum_charge, created_by, notes) VALUES
-- Ocean Freight Container Pricing
('ocean', '20ft', 'container', 150.00, 200.00, 'container', 350.00, 'system', 'Standard 20ft container pricing'),
('ocean', '40ft', 'container', 200.00, 300.00, 'container', 500.00, 'system', 'Standard 40ft container pricing'),
('ocean', '40ft_hc', 'container', 250.00, 350.00, 'container', 600.00, 'system', 'High cube 40ft container pricing'),

-- Air Freight Weight-Based Pricing
('air', NULL, 'weight', 1.00, 1.50, 'kg', 150.00, 'system', 'Air freight per kg pricing'),

-- Loose Cargo Weight-Based Pricing
('loose_cargo', NULL, 'weight', 0.50, 0.75, 'kg', 100.00, 'system', 'Loose cargo per kg pricing');

-- Create manual override audit table
CREATE TABLE IF NOT EXISTS pricing_overrides (
    id SERIAL PRIMARY KEY,
    bill_of_lading_id INTEGER REFERENCES bill_of_lading(id),
    original_ctn_fee DECIMAL(10,2),
    original_service_fee DECIMAL(10,2),
    new_ctn_fee DECIMAL(10,2),
    new_service_fee DECIMAL(10,2),
    reason TEXT NOT NULL,
    overridden_by VARCHAR(100) NOT NULL,
    overridden_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_shipment_type ON bill_of_lading(shipment_type);
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_container_type ON bill_of_lading(container_type);
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_pricing_method ON bill_of_lading(pricing_method);
CREATE INDEX IF NOT EXISTS idx_pricing_config_active ON pricing_config(is_active);
CREATE INDEX IF NOT EXISTS idx_pricing_overrides_bill_id ON pricing_overrides(bill_of_lading_id);

-- Add comments for documentation
COMMENT ON TABLE pricing_config IS 'Configuration table for different pricing methods and rates';
COMMENT ON COLUMN bill_of_lading.shipment_type IS 'Type of shipment: ocean, air, or loose_cargo';
COMMENT ON COLUMN bill_of_lading.container_type IS 'Container type: 20ft, 40ft, 40ft_hc, or loose_cargo';
COMMENT ON COLUMN bill_of_lading.pricing_method IS 'Method used for fee calculation: container, weight, or mixed';
COMMENT ON COLUMN bill_of_lading.manual_override IS 'Flag indicating if fees were manually overridden';
COMMENT ON COLUMN bill_of_lading.pricing_calculation_log IS 'JSON log of how fees were calculated for audit purposes'; 