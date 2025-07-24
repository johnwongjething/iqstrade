CREATE TABLE IF NOT EXISTS unmatched_receipts (
    id SERIAL PRIMARY KEY,
    date DATE,
    description TEXT,
    amount NUMERIC(10, 2),
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_text TEXT
);

COMMENT ON TABLE unmatched_receipts IS 'Stores details of payment receipts that could not be automatically matched to a Bill of Lading.';
COMMENT ON COLUMN unmatched_receipts.reason IS 'The reason why the receipt could not be matched, e.g., Invalid BL number, amount mismatch.';
COMMENT ON COLUMN unmatched_receipts.raw_text IS 'The full text of the email body for manual review.'; 