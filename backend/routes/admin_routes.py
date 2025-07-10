from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.security import decrypt_sensitive_data
from config import get_db_conn  # Updated import
import json

admin_routes = Blueprint('admin_routes', __name__)

# Admin-only endpoints

@admin_routes.route('/admin/users', methods=['GET'])
@jwt_required()
def get_users():
    user = json.loads(get_jwt_identity())
    if user['role'] not in ['admin']:
        return jsonify({'error': 'Admins only!'}), 403
    conn = get_db_conn()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cur = conn.cursor()
    cur.execute("SELECT id, username, customer_name, customer_email, customer_phone, role, approved FROM users")
    users = []
    for row in cur.fetchall():
        decrypted_email = decrypt_sensitive_data(row[3]) if row[3] is not None else ''
        decrypted_phone = decrypt_sensitive_data(row[4]) if row[4] is not None else ''
        users.append({
            'id': row[0],
            'username': row[1],
            'customer_name': row[2],
            'customer_email': decrypted_email,
            'customer_phone': decrypted_phone,
            'role': row[5],
            'approved': row[6]
        })
    cur.close()
    conn.close()
    return jsonify(users)

@admin_routes.route('/admin/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    user = json.loads(get_jwt_identity())
    if user['role'] not in ['admin']:
        return jsonify({'error': 'Admins only!'}), 403
    conn = get_db_conn()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'User deleted'})

@admin_routes.route('/admin/approve/<int:user_id>', methods=['POST'])
@jwt_required()
def approve_user(user_id):
    user = json.loads(get_jwt_identity())
    if user['role'] not in ['admin']:
        return jsonify({'error': 'Admins only!'}), 403
    conn = get_db_conn()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cur = conn.cursor()
    cur.execute("UPDATE users SET approved=TRUE WHERE id=%s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'User approved'})
