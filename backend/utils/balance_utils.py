"""
Customer Balance Management Utilities
Handles all customer balance operations without affecting existing business logic
"""
import logging
from decimal import Decimal
from config import get_db_conn
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

def get_customer_balance(username):
    """Get current balance for a customer"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT balance_amount FROM customer_balances 
            WHERE username = %s AND is_active = true
        """, (username,))
        
        result = cursor.fetchone()
        return float(result[0]) if result else 0.0
        
    except Exception as e:
        logger.error(f"Error getting balance for {username}: {e}")
        return 0.0
    finally:
        cursor.close()
        conn.close()

def update_customer_balance(username, amount, transaction_type, reference_type=None, 
                          reference_id=None, payment_source=None, description=None, created_by=None):
    """Update customer balance and create transaction record"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN")
        
        # Get current balance
        cursor.execute("""
            SELECT balance_amount FROM customer_balances 
            WHERE username = %s AND is_active = true
        """, (username,))
        
        result = cursor.fetchone()
        current_balance = Decimal(result[0]) if result else Decimal('0.00')
        
        # Calculate new balance
        amount_decimal = Decimal(str(amount))
        if transaction_type == 'credit':
            new_balance = current_balance + amount_decimal
        elif transaction_type == 'debit':
            new_balance = current_balance - amount_decimal
        elif transaction_type == 'adjustment':
            new_balance = amount_decimal  # Direct adjustment
        elif transaction_type == 'application':
            new_balance = current_balance - amount_decimal  # Apply credit
        else:
            raise ValueError(f"Invalid transaction type: {transaction_type}")
        
        # Update or insert balance
        cursor.execute("""
            INSERT INTO customer_balances (username, balance_amount, last_updated, notes)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (username) 
            DO UPDATE SET 
                balance_amount = %s,
                last_updated = %s
        """, (username, new_balance, datetime.now(pytz.timezone('Asia/Hong_Kong')), 
              f"Updated by {transaction_type}", new_balance, datetime.now(pytz.timezone('Asia/Hong_Kong'))))
        
        # Create transaction record
        cursor.execute("""
            INSERT INTO customer_balance_transactions 
            (username, transaction_type, amount, reference_type, reference_id, 
             payment_source, description, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (username, transaction_type, amount_decimal, reference_type, reference_id,
              payment_source, description, created_by))
        
        # Commit transaction
        cursor.execute("COMMIT")
        
        logger.info(f"Balance updated for {username}: {current_balance} -> {new_balance} ({transaction_type}: {amount})")
        return float(new_balance)
        
    except Exception as e:
        cursor.execute("ROLLBACK")
        logger.error(f"Error updating balance for {username}: {e}")
        raise
    finally:
        cursor.close()

def process_payment_balance(username, payment_amount, invoice_amount, bl_id, payment_source, created_by=None):
    """Process payment and calculate balance adjustments"""
    try:
        payment_decimal = Decimal(str(payment_amount))
        invoice_decimal = Decimal(str(invoice_amount))
        
        if payment_decimal > invoice_decimal:
            # Overpayment - create credit
            credit_amount = payment_decimal - invoice_decimal
            update_customer_balance(
                username=username,
                amount=float(credit_amount),
                transaction_type='credit',
                reference_type='payment_match',
                reference_id=bl_id,
                payment_source=payment_source,
                description=f'Overpayment credit: Paid ${payment_amount}, Invoice ${invoice_amount}',
                created_by=created_by
            )
            return float(credit_amount)
            
        elif payment_decimal < invoice_decimal:
            # Underpayment - create debit
            debit_amount = invoice_decimal - payment_decimal
            update_customer_balance(
                username=username,
                amount=float(debit_amount),
                transaction_type='debit',
                reference_type='payment_match',
                reference_id=bl_id,
                payment_source=payment_source,
                description=f'Underpayment debit: Paid ${payment_amount}, Invoice ${invoice_amount}',
                created_by=created_by
            )
            return -float(debit_amount)
            
        else:
            # Exact payment - no balance adjustment
            return 0.0
            
    except Exception as e:
        logger.error(f"Error processing payment balance: {e}")
        return 0.0

def get_customer_balance_history(username, limit=50):
    """Get transaction history for a customer"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT transaction_type, amount, reference_type, payment_source, 
                   description, created_at, created_by
            FROM customer_balance_transactions 
            WHERE username = %s 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (username, limit))
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'transaction_type': row[0],
                'amount': float(row[1]),
                'reference_type': row[2],
                'payment_source': row[3],
                'description': row[4],
                'created_at': row[5].isoformat() if row[5] else None,
                'created_by': row[6]
            })
        
        return transactions
        
    except Exception as e:
        logger.error(f"Error getting balance history for {username}: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def check_payment_processed(bl_id, payment_source):
    """Check if payment has already been processed to prevent duplicates"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id FROM customer_balance_transactions 
            WHERE reference_id = %s AND payment_source = %s
        """, (bl_id, payment_source))
        
        result = cursor.fetchone()
        if result:
            logger.warning(f"Payment already processed for BL {bl_id} via {payment_source}")
            return True
        return False
        
    except Exception as e:
        logger.error(f"Error checking payment processed status: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def mark_payment_processed(bl_id, payment_source, processed_by):
    """Mark payment as processed to prevent duplicates"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Get customer_username from bill_of_lading table
        cursor.execute("""
            SELECT customer_username FROM bill_of_lading WHERE id = %s
        """, (bl_id,))
        
        result = cursor.fetchone()
        if result:
            customer_username = result[0]
            
            # Use customer_username if available, otherwise use processed_by
            username = customer_username or processed_by
            
            # If username is still None, use a default system user
            if not username:
                username = 'system'
        else:
            username = processed_by or 'system'
        
        # Insert a record in customer_balance_transactions to mark as processed
        cursor.execute("""
            INSERT INTO customer_balance_transactions 
            (username, transaction_type, amount, reference_type, reference_id, payment_source, description, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (username, 'credit', 0, 'bill_of_lading', bl_id, payment_source, f'Payment marked as processed for BL {bl_id}', processed_by))
        
        conn.commit()
        logger.info(f"Payment marked as processed for BL {bl_id} by {processed_by} using username {username}")
        
    except Exception as e:
        logger.error(f"Error marking payment as processed for BL {bl_id}: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close() 