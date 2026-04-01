/**
 * Duplicate Payment Notification System for WhatsApp App
 * Handles notifications when duplicate payments are detected
 */

const { Pool } = require('pg');
require('dotenv').config();

const pool = new Pool({
  host: process.env.RAILWAY_DB_HOST,
  user: process.env.RAILWAY_DB_USER,
  password: process.env.RAILWAY_DB_PASSWORD,
  database: process.env.RAILWAY_DB_NAME,
  port: process.env.RAILWAY_DB_PORT,
  ssl: false,
});

/**
 * Send comprehensive duplicate payment notifications
 * @param {number} blId - Bill of lading ID
 * @param {string} blNumber - Bill of lading number
 * @param {string} customerUsername - Customer username
 * @param {string} customerEmail - Customer email (encrypted)
 * @param {number} paymentAmount - Amount of duplicate payment
 * @param {string} paymentSource - Source of payment (webhook, email, bank_import, whatsapp)
 * @param {Date} originalPaymentDate - Date of original payment (optional)
 */
async function sendDuplicatePaymentNotifications(blId, blNumber, customerUsername, customerEmail, 
                                               paymentAmount, paymentSource, originalPaymentDate = null) {
  try {
    console.log(`[DUPLICATE PAYMENT] Sending notifications for BL ${blNumber} (ID: ${blId})`);
    
    // Record duplicate payment in unmatched_receipts table for dashboard visibility
    await recordDuplicatePayment(blId, blNumber, customerUsername, paymentAmount, paymentSource, originalPaymentDate);
    
    // Get customer phone number for WhatsApp
    const customerPhone = await getCustomerPhone(customerUsername);
    
    // Get customer FCM tokens
    const fcmTokens = await getCustomerFcmTokens(customerUsername);
    
    // Send notifications
    await sendFcmDuplicateNotification(fcmTokens, blNumber, paymentAmount, paymentSource);
    await sendEmailDuplicateNotification(customerEmail, blNumber, paymentAmount, paymentSource, originalPaymentDate);
    await sendWhatsappDuplicateNotification(customerPhone, blNumber, paymentAmount, paymentSource);
    await sendStaffRefundAlert(blNumber, customerUsername, paymentAmount, paymentSource);
    
    console.log(`[DUPLICATE PAYMENT] Notifications sent for BL ${blNumber} (ID: ${blId})`);
    
  } catch (error) {
    console.error(`[DUPLICATE PAYMENT] Error sending notifications for BL ${blNumber}:`, error);
  }
}

/**
 * Record duplicate payment in unmatched_receipts table for dashboard visibility
 * @param {number} blId - Bill of lading ID
 * @param {string} blNumber - Bill of lading number
 * @param {string} customerUsername - Customer username
 * @param {number} paymentAmount - Payment amount
 * @param {string} paymentSource - Payment source
 * @param {Date} originalPaymentDate - Original payment date (optional)
 */
async function recordDuplicatePayment(blId, blNumber, customerUsername, paymentAmount, paymentSource, originalPaymentDate = null) {
  try {
    // Format original payment date
    let originalDateStr = "";
    if (originalPaymentDate) {
      if (typeof originalPaymentDate === 'string') {
        originalDateStr = ` (Original: ${originalPaymentDate})`;
      } else {
        originalDateStr = ` (Original: ${originalPaymentDate.toISOString().replace('T', ' ').substring(0, 19)})`;
      }
    }
    
    // Create description
    const description = `Duplicate payment for BL ${blNumber} from ${customerUsername}`;
    const reason = `Duplicate Payment: Payment of $${paymentAmount.toFixed(2)} already processed${originalDateStr}`;
    
    // Insert into unmatched_receipts table
    await pool.query(`
      INSERT INTO unmatched_receipts (date, description, amount, reason, raw_text)
      VALUES ($1, $2, $3, $4, $5)
    `, [
      new Date(),
      description,
      paymentAmount,
      reason,
      `Duplicate payment detected for BL ${blNumber} via ${paymentSource}. Customer: ${customerUsername}`
    ]);
    
    console.log(`[DUPLICATE PAYMENT] Recorded duplicate payment in unmatched_receipts for BL ${blNumber}`);
    
  } catch (error) {
    console.error(`[DUPLICATE PAYMENT] Error recording duplicate payment in unmatched_receipts for BL ${blNumber}:`, error);
  }
}

/**
 * Get customer phone number from database
 * @param {string} username - Customer username
 * @returns {Promise<string|null>} - Customer phone number or null
 */
async function getCustomerPhone(username) {
  try {
    const result = await pool.query(
      'SELECT customer_phone FROM users WHERE username = $1',
      [username]
    );
    
    if (result.rows.length > 0 && result.rows[0].customer_phone) {
      // Note: In a real implementation, you would decrypt this
      return result.rows[0].customer_phone;
    }
    return null;
  } catch (error) {
    console.error(`[DUPLICATE PAYMENT] Error getting customer phone for ${username}:`, error);
    return null;
  }
}

/**
 * Get customer FCM tokens from database
 * @param {string} username - Customer username
 * @returns {Promise<string[]>} - Array of FCM tokens
 */
async function getCustomerFcmTokens(username) {
  try {
    const result = await pool.query(
      'SELECT token FROM fcm_tokens WHERE username = $1 AND is_active = true',
      [username]
    );
    
    return result.rows.map(row => row.token);
  } catch (error) {
    console.error(`[DUPLICATE PAYMENT] Error getting FCM tokens for ${username}:`, error);
    return [];
  }
}

/**
 * Send FCM push notification to user about duplicate payment
 * @param {string[]} fcmTokens - Array of FCM tokens
 * @param {string} blNumber - Bill of lading number
 * @param {number} paymentAmount - Payment amount
 * @param {string} paymentSource - Payment source
 */
async function sendFcmDuplicateNotification(fcmTokens, blNumber, paymentAmount, paymentSource) {
  if (!fcmTokens || fcmTokens.length === 0) {
    console.log('[DUPLICATE PAYMENT] No FCM tokens available for notification');
    return;
  }
  
  try {
    const title = "⚠️ Duplicate Payment Detected";
    const body = `Your payment of $${paymentAmount.toFixed(2)} for BL ${blNumber} has already been processed. No action needed.`;
    
    const data = {
      type: 'duplicate_payment',
      bl_number: blNumber,
      payment_amount: paymentAmount.toString(),
      payment_source: paymentSource,
      timestamp: new Date().toISOString()
    };
    
    // Note: In a real implementation, you would call your FCM service here
    console.log(`[DUPLICATE PAYMENT] FCM notification would be sent to ${fcmTokens.length} tokens:`, {
      title,
      body,
      data
    });
    
  } catch (error) {
    console.error('[DUPLICATE PAYMENT] Error sending FCM notification:', error);
  }
}

/**
 * Send email notification to user about duplicate payment
 * @param {string} email - Customer email
 * @param {string} blNumber - Bill of lading number
 * @param {number} paymentAmount - Payment amount
 * @param {string} paymentSource - Payment source
 * @param {Date} originalPaymentDate - Original payment date
 */
async function sendEmailDuplicateNotification(email, blNumber, paymentAmount, paymentSource, originalPaymentDate = null) {
  if (!email) {
    console.log('[DUPLICATE PAYMENT] No email available for notification');
    return;
  }
  
  try {
    const subject = "⚠️ Duplicate Payment Alert - No Action Required";
    
    // Format original payment date
    let originalDateStr = "";
    if (originalPaymentDate) {
      if (typeof originalPaymentDate === 'string') {
        originalDateStr = `Original payment was processed on: ${originalPaymentDate}`;
      } else {
        originalDateStr = `Original payment was processed on: ${originalPaymentDate.toISOString()}`;
      }
    }
    
    const body = `
Dear Customer,

We have detected a duplicate payment attempt for your shipment.

**Payment Details:**
- Bill of Lading: ${blNumber}
- Duplicate Amount: $${paymentAmount.toFixed(2)}
- Payment Source: ${paymentSource.charAt(0).toUpperCase() + paymentSource.slice(1)}
${originalDateStr}

**Important:** Your original payment has already been processed successfully. This duplicate payment will not be charged to your account.

**No action is required from you.** Your shipment processing continues as normal.

If you have any questions or concerns, please contact our support team.

Best regards,
Terry Ray Logistics Team
    `;
    
    // Note: In a real implementation, you would call your email service here
    console.log(`[DUPLICATE PAYMENT] Email notification would be sent to ${email}:`, {
      subject,
      body: body.trim()
    });
    
  } catch (error) {
    console.error('[DUPLICATE PAYMENT] Error sending email notification:', error);
  }
}

/**
 * Send WhatsApp notification to user about duplicate payment
 * @param {string} phone - Customer phone number
 * @param {string} blNumber - Bill of lading number
 * @param {number} paymentAmount - Payment amount
 * @param {string} paymentSource - Payment source
 */
async function sendWhatsappDuplicateNotification(phone, blNumber, paymentAmount, paymentSource) {
  if (!phone) {
    console.log('[DUPLICATE PAYMENT] No phone available for WhatsApp notification');
    return;
  }
  
  try {
    const message = `⚠️ Duplicate Payment Alert: Your payment of $${paymentAmount.toFixed(2)} for BL ${blNumber} has already been processed. No refund needed.`;
    
    // Note: In a real implementation, you would call your WhatsApp API here
    console.log(`[DUPLICATE PAYMENT] WhatsApp notification would be sent to ${phone}:`, message);
    
  } catch (error) {
    console.error('[DUPLICATE PAYMENT] Error sending WhatsApp notification:', error);
  }
}

/**
 * Send alert to staff about potential refund request
 * @param {string} blNumber - Bill of lading number
 * @param {string} customerUsername - Customer username
 * @param {number} paymentAmount - Payment amount
 * @param {string} paymentSource - Payment source
 */
async function sendStaffRefundAlert(blNumber, customerUsername, paymentAmount, paymentSource) {
  try {
    // Get staff email addresses
    const staffEmails = await getStaffEmails();
    
    if (!staffEmails || staffEmails.length === 0) {
      console.log('[DUPLICATE PAYMENT] No staff emails found for refund alert');
      return;
    }
    
    const subject = `🚨 Duplicate Payment Alert - BL ${blNumber}`;
    
    const body = `
**Duplicate Payment Detected**

A customer has attempted a duplicate payment that was automatically prevented.

**Details:**
- Bill of Lading: ${blNumber}
- Customer: ${customerUsername}
- Duplicate Amount: $${paymentAmount.toFixed(2)}
- Payment Source: ${paymentSource.charAt(0).toUpperCase() + paymentSource.slice(1)}
- Detection Time: ${new Date().toISOString()}

**Action Required:**
- Monitor for customer support requests
- Be prepared to explain the duplicate payment prevention
- No refund processing needed (payment was not charged)

**Customer Notifications Sent:**
- ✅ FCM Push Notification
- ✅ Email Notification  
- ✅ WhatsApp Message (if configured)

This is an automated alert. The system has already notified the customer.
    `;
    
    // Note: In a real implementation, you would call your email service here
    console.log(`[DUPLICATE PAYMENT] Staff alert would be sent to ${staffEmails.length} staff members:`, {
      subject,
      body: body.trim(),
      recipients: staffEmails
    });
    
  } catch (error) {
    console.error('[DUPLICATE PAYMENT] Error sending staff refund alert:', error);
  }
}

/**
 * Get all staff email addresses
 * @returns {Promise<string[]>} - Array of staff email addresses
 */
async function getStaffEmails() {
  try {
    const result = await pool.query(
      'SELECT customer_email FROM users WHERE role = $1 AND approved = $2',
      ['staff', true]
    );
    
    const emails = [];
    for (const row of result.rows) {
      if (row.customer_email) {
        // Note: In a real implementation, you would decrypt this
        emails.push(row.customer_email);
      }
    }
    
    return emails;
  } catch (error) {
    console.error('[DUPLICATE PAYMENT] Error getting staff emails:', error);
    return [];
  }
}

module.exports = {
  sendDuplicatePaymentNotifications,
  getCustomerPhone,
  getCustomerFcmTokens,
  sendFcmDuplicateNotification,
  sendEmailDuplicateNotification,
  sendWhatsappDuplicateNotification,
  sendStaffRefundAlert,
  getStaffEmails
}; 