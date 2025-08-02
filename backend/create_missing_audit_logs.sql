-- Create missing audit_logs table for performance monitoring
-- Run this on your Railway PostgreSQL database

-- Create audit_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    operation VARCHAR(255) NOT NULL,
    details TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45)
);

-- Add comments for documentation
COMMENT ON TABLE audit_logs IS 'System activity tracking for security and performance monitoring';
COMMENT ON COLUMN audit_logs.user_id IS 'Reference to users table (can be NULL for system operations)';
COMMENT ON COLUMN audit_logs.operation IS 'Type of operation performed (login, logout, data_access, etc.)';
COMMENT ON COLUMN audit_logs.details IS 'Additional details about the operation';
COMMENT ON COLUMN audit_logs.timestamp IS 'When the operation occurred';
COMMENT ON COLUMN audit_logs.ip_address IS 'IP address of the user performing the operation';

-- Create indexes for audit_logs table
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_operation ON audit_logs(operation);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_operation ON audit_logs(user_id, operation);

-- Insert a sample audit log entry to verify the table works
INSERT INTO audit_logs (user_id, operation, details, ip_address) 
VALUES (NULL, 'table_creation', 'audit_logs table created for performance monitoring', 'system')
ON CONFLICT DO NOTHING;

-- Verify the table was created
SELECT 
    table_name, 
    column_name, 
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'audit_logs' 
ORDER BY ordinal_position;

-- Show the sample record
SELECT * FROM audit_logs LIMIT 5; 