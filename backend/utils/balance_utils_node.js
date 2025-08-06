/**
 * Node.js version of balance utilities for WhatsApp chatHandler
 * Provides duplicate payment protection and balance processing
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
 * Check if a payment has already been processed for a specific BL and payment source
 * @param {number} blId - Bill of lading ID
 * @param {string} paymentSource - Source of payment (webhook, email, bank_import, whatsapp)
 * @returns {Promise<boolean>} - True if payment already processed
 */
async function checkPaymentProcessed(blId, paymentSource) {
  try {
    const result = await pool.query(
      'SELECT COUNT(*) FROM customer_balance_transactions WHERE bl_id = $1 AND payment_source = $2',
      [blId, paymentSource]
    );
    return parseInt(result.rows[0].count) > 0;
  } catch (error) {
    console.error('Error checking payment processed:', error);
    return false;
  }
}

/**
 * Mark a payment as processed
 * @param {number} blId - Bill of lading ID
 * @param {string} paymentSource - Source of payment
 * @param {string} createdBy - Who created the payment record
 */
async function markPaymentProcessed(blId, paymentSource, createdBy) {
  try {
    await pool.query(
      'INSERT INTO customer_balance_transactions (bl_id, payment_source, created_by) VALUES ($1, $2, $3)',
      [blId, paymentSource, createdBy]
    );
    console.log(`Payment marked as processed for BL ${blId} from ${paymentSource}`);
  } catch (error) {
    console.error('Error marking payment as processed:', error);
  }
}

/**
 * Process payment balance for a customer
 * @param {string} username - Customer username
 * @param {number} paymentAmount - Amount paid
 * @param {number} invoiceAmount - Total invoice amount
 * @param {number} blId - Bill of lading ID
 * @param {string} paymentSource - Source of payment
 * @param {string} createdBy - Who created the payment record
 * @returns {Promise<number>} - Balance adjustment amount
 */
async function processPaymentBalance(username, paymentAmount, invoiceAmount, blId, paymentSource, createdBy) {
  try {
    // Get current balance
    const balanceResult = await pool.query(
      'SELECT balance_amount FROM customer_balances WHERE username = $1',
      [username]
    );
    
    let currentBalance = 0;
    if (balanceResult.rows.length > 0) {
      currentBalance = parseFloat(balanceResult.rows[0].balance_amount || 0);
    } else {
      // Create balance record if it doesn't exist
      await pool.query(
        'INSERT INTO customer_balances (username, balance_amount) VALUES ($1, $2)',
        [username, 0]
      );
    }
    
    // Calculate balance adjustment
    const balanceAdjustment = paymentAmount - invoiceAmount;
    const newBalance = currentBalance + balanceAdjustment;
    
    // Update balance
    await pool.query(
      'UPDATE customer_balances SET balance_amount = $1, last_updated = CURRENT_TIMESTAMP WHERE username = $2',
      [newBalance, username]
    );
    
    // Record transaction
    await pool.query(
      `INSERT INTO customer_balance_transactions 
       (username, transaction_type, amount, reference_type, reference_id, payment_source, description, created_by)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
      [
        username,
        balanceAdjustment >= 0 ? 'credit' : 'debit',
        Math.abs(balanceAdjustment),
        'bill_of_lading',
        blId,
        paymentSource,
        `Payment processing for BL ${blId}`,
        createdBy
      ]
    );
    
    console.log(`Balance processed for ${username}: adjustment ${balanceAdjustment}, new balance ${newBalance}`);
    return balanceAdjustment;
    
  } catch (error) {
    console.error('Error processing payment balance:', error);
    return 0;
  }
}

/**
 * Get customer email for notifications
 * @param {number} blId - Bill of lading ID
 * @returns {Promise<string|null>} - Customer email or null
 */
async function getCustomerEmail(blId) {
  try {
    const result = await pool.query(
      'SELECT customer_email FROM bill_of_lading WHERE id = $1',
      [blId]
    );
    return result.rows[0]?.customer_email || null;
  } catch (error) {
    console.error('Error getting customer email:', error);
    return null;
  }
}

/**
 * Get customer username for notifications
 * @param {number} blId - Bill of lading ID
 * @returns {Promise<string|null>} - Customer username or null
 */
async function getCustomerUsername(blId) {
  try {
    const result = await pool.query(
      'SELECT customer_username FROM bill_of_lading WHERE id = $1',
      [blId]
    );
    return result.rows[0]?.customer_username || null;
  } catch (error) {
    console.error('Error getting customer username:', error);
    return null;
  }
}

/**
 * Get original payment date for duplicate notifications
 * @param {number} blId - Bill of lading ID
 * @param {string} paymentSource - Payment source
 * @returns {Promise<Date|null>} - Original payment date or null
 */
async function getOriginalPaymentDate(blId, paymentSource) {
  try {
    const result = await pool.query(
      'SELECT created_at FROM customer_balance_transactions WHERE bl_id = $1 AND payment_source = $2 ORDER BY created_at DESC LIMIT 1',
      [blId, paymentSource]
    );
    return result.rows[0]?.created_at || null;
  } catch (error) {
    console.error('Error getting original payment date:', error);
    return null;
  }
}

module.exports = {
  checkPaymentProcessed,
  markPaymentProcessed,
  processPaymentBalance,
  getCustomerEmail,
  getCustomerUsername,
  getOriginalPaymentDate
}; 