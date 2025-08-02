-- Create FCM notifications tracking table to prevent duplicate notifications
CREATE TABLE IF NOT EXISTS fcm_notifications (
    id SERIAL PRIMARY KEY,
    email_id INTEGER NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_fcm_notifications_email_type ON fcm_notifications(email_id, notification_type);
CREATE INDEX IF NOT EXISTS idx_fcm_notifications_sent_at ON fcm_notifications(sent_at);

-- Add comment
COMMENT ON TABLE fcm_notifications IS 'Tracks FCM notifications sent to prevent duplicates';
COMMENT ON COLUMN fcm_notifications.email_id IS 'ID of the email that triggered the notification';
COMMENT ON COLUMN fcm_notifications.notification_type IS 'Type of notification (new_email, payment_receipt, etc.)';
COMMENT ON COLUMN fcm_notifications.sent_at IS 'When the notification was sent'; 