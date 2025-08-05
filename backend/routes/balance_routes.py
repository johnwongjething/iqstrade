"""
Customer Balance API Routes
Handles all customer balance operations
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.balance_utils import (
    get_customer_balance, 
    update_customer_balance, 
    get_customer_balance_history,
    process_payment_balance
)
from config import get_db_conn
from utils.security import decrypt_sensitive_data
import logging

balance_routes = Blueprint('balance_routes', __name__)
logger = logging.getLogger(__name__)

@balance_routes.route('/balance/<username>', methods=['GET'])
@jwt_required()
def get_balance(username):
    """Get customer balance"""
    try:
        balance = get_customer_balance(username)
        
        # Get additional balance info for frontend compatibility
        conn = get_db_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT balance_amount, last_updated 
                FROM customer_balances 
                WHERE username = %s AND is_active = true
            """, (username,))
            result = cursor.fetchone()
            
            return jsonify({
                'username': username,
                'balance': balance,
                'balance_amount': balance,  # Frontend compatibility
                'last_updated': result[1].isoformat() if result and result[1] else None,
                'status': 'success'
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        logger.error(f"Error getting balance for {username}: {e}")
        return jsonify({'error': 'Failed to get balance'}), 500

@balance_routes.route('/balance/<username>/history', methods=['GET'])
@jwt_required()
def get_balance_history(username):
    """Get customer balance transaction history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        history = get_customer_balance_history(username, limit)
        return jsonify({
            'username': username,
            'transactions': history,
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error getting balance history for {username}: {e}")
        return jsonify({'error': 'Failed to get balance history'}), 500

@balance_routes.route('/balance/<username>/adjust', methods=['POST'])
@jwt_required()
def adjust_balance(username):
    """Manually adjust customer balance"""
    try:
        data = request.get_json()
        amount = data.get('amount')
        transaction_type = data.get('transaction_type')  # 'credit', 'debit', 'adjustment'
        description = data.get('description', 'Manual adjustment')
        created_by = get_jwt_identity()
        
        if not amount or not transaction_type:
            return jsonify({'error': 'Amount and transaction_type are required'}), 400
        
        if transaction_type not in ['credit', 'debit', 'adjustment']:
            return jsonify({'error': 'Invalid transaction_type'}), 400
        
        new_balance = update_customer_balance(
            username=username,
            amount=amount,
            transaction_type=transaction_type,
            reference_type='manual_adjustment',
            description=description,
            created_by=created_by
        )
        
        return jsonify({
            'username': username,
            'new_balance': new_balance,
            'adjustment_amount': amount,
            'transaction_type': transaction_type,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error adjusting balance for {username}: {e}")
        return jsonify({'error': 'Failed to adjust balance'}), 500

@balance_routes.route('/balance/<username>/apply', methods=['POST'])
@jwt_required()
def apply_balance(username):
    """Apply customer balance to invoice"""
    try:
        data = request.get_json()
        amount = data.get('amount')
        bl_id = data.get('bl_id')
        description = data.get('description', 'Balance applied to invoice')
        created_by = get_jwt_identity()
        
        if not amount or not bl_id:
            return jsonify({'error': 'Amount and bl_id are required'}), 400
        
        new_balance = update_customer_balance(
            username=username,
            amount=amount,
            transaction_type='application',
            reference_type='invoice_application',
            reference_id=bl_id,
            description=description,
            created_by=created_by
        )
        
        return jsonify({
            'username': username,
            'new_balance': new_balance,
            'applied_amount': amount,
            'bl_id': bl_id,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error applying balance for {username}: {e}")
        return jsonify({'error': 'Failed to apply balance'}), 500

@balance_routes.route('/balance/search', methods=['GET'])
@jwt_required()
def search_customers():
    """Search customers by name for balance lookup"""
    try:
        search_term = request.args.get('q', '')
        if not search_term:
            return jsonify({'error': 'Search term is required'}), 400
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Search by username, customer name, or customer email
        cursor.execute("""
            SELECT u.username, u.customer_name, u.customer_email, 
                   COALESCE(cb.balance_amount, 0) as balance
            FROM users u
            LEFT JOIN customer_balances cb ON u.username = cb.username
            WHERE u.username ILIKE %s 
               OR u.customer_name ILIKE %s 
               OR u.customer_email ILIKE %s
            ORDER BY u.username
            LIMIT 20
        """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        
        customers = []
        for row in cursor.fetchall():
            # Decrypt the email address
            encrypted_email = row[2]
            decrypted_email = 'N/A'
            if encrypted_email:
                try:
                    decrypted_email = decrypt_sensitive_data(encrypted_email)
                except Exception as e:
                    logger.warning(f"Failed to decrypt email for {row[0]}: {e}")
                    decrypted_email = 'N/A'
            
            customers.append({
                'username': row[0],
                'customer_name': row[1] or 'N/A',
                'email': decrypted_email,  # Decrypted email address
                'balance_amount': float(row[3]) if row[3] else 0.0
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'customers': customers,
            'search_term': search_term,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error searching customers: {e}")
        return jsonify({'error': 'Failed to search customers'}), 500

@balance_routes.route('/balance/all', methods=['GET'])
@jwt_required()
def get_all_balances():
    """Get all customer balances (for admin view)"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.username, u.customer_name, u.customer_email, 
                   COALESCE(cb.balance_amount, 0) as balance,
                   cb.last_updated
            FROM users u
            LEFT JOIN customer_balances cb ON u.username = cb.username
            WHERE u.role = 'customer'
            ORDER BY cb.balance_amount DESC NULLS LAST
        """)
        
        balances = []
        for row in cursor.fetchall():
            # Decrypt the email address
            encrypted_email = row[2]
            decrypted_email = 'N/A'
            if encrypted_email:
                try:
                    decrypted_email = decrypt_sensitive_data(encrypted_email)
                except Exception as e:
                    logger.warning(f"Failed to decrypt email for {row[0]}: {e}")
                    decrypted_email = 'N/A'
            
            balances.append({
                'username': row[0],
                'customer_name': row[1],
                'customer_email': decrypted_email,  # Decrypted email address
                'balance': float(row[3]) if row[3] else 0.0,
                'last_updated': row[4].isoformat() if row[4] else None
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'balances': balances,
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error getting all balances: {e}")
        return jsonify({'error': 'Failed to get balances'}), 500 