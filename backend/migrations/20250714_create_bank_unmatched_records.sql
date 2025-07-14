CREATE TABLE IF NOT EXISTS bank_unmatched_records (
    id SERIAL PRIMARY KEY,
    date TEXT,
    description TEXT,
    amount NUMERIC,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
