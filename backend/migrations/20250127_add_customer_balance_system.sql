-- CustomerBalance System Migration
-- Date: 2025-01-27
-- Purpose: Add customer balance tracking without affecting existing business logic

-- Add processing status tracking to existing tables
ALTER TABLE bill_of_lading ADD COLUMN IF NOT EXISTS payment_processed_by VARCHAR(50);
ALTER TABLE bill_of_lading ADD COLUMN IF NOT EXISTS payment_processed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE bill_of_lading ADD COLUMN IF NOT EXISTS payment_source VARCHAR(50);

-- Create Customer Balance Table
CREATE TABLE IF NOT EXISTS customer_balances (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL REFERENCES users(username),
    balance_amount NUMERIC(10,2) DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    is_active BOOLEAN DEFAULT true
);

-- Create Customer Balance Transactions Table
CREATE TABLE IF NOT EXISTS customer_balance_transactions (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL REFERENCES users(username),
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('credit', 'debit', 'adjustment', 'application')),
    amount NUMERIC(10,2) NOT NULL,
    reference_type VARCHAR(50), -- 'payment_match', 'manual_adjustment', 'invoice_application'
    reference_id INTEGER, -- bill_of_lading.id or null
    payment_source VARCHAR(50), -- 'email', 'whatsapp', 'bank_import', 'webhook'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_customer_balances_username ON customer_balances(username);
CREATE INDEX IF NOT EXISTS idx_customer_balance_transactions_username ON customer_balance_transactions(username);
CREATE INDEX IF NOT EXISTS idx_customer_balance_transactions_created_at ON customer_balance_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bill_of_lading_payment_processed ON bill_of_lading(payment_processed_by, payment_processed_at);

-- Add unique constraint to prevent duplicate balances per user
ALTER TABLE customer_balances ADD CONSTRAINT customer_balances_username_unique UNIQUE (username);

-- Initialize customer balances for existing users (set to 0 to avoid system crash)
INSERT INTO customer_balances (username, balance_amount, notes)
SELECT username, 0, 'Initialized for existing user'
FROM users 
WHERE username NOT IN (SELECT username FROM customer_balances)
ON CONFLICT (username) DO NOTHING; 