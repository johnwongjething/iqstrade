
from flask import Blueprint, request, jsonify, g, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import get_db_conn
import json
import logging
from email_utils import send_simple_email

email_routes = Blueprint('email_routes', __name__)

# --- Permissions Helper ---
def require_staff():
    # Example: check user role from JWT or DB
    user = get_jwt_identity()
    if not user or (isinstance(user, dict) and user.get('role') not in ['staff', 'admin']):
        abort(403, description='Forbidden')

@email_routes.route('/inbox', methods=['GET'])
@jwt_required()
def inbox():
    require_staff()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, sender, subject, created_at, bl_numbers
        FROM customer_emails
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    emails = [
        {
            'id': row[0],
            'sender': row[1],
            'subject': row[2],
            'created_at': row[3],
            'bl_numbers': row[4]
        } for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    logging.debug(f"[INBOX] Fetched {len(emails)} emails")
    return jsonify(emails)

@email_routes.route('/<int:email_id>', methods=['GET'])
@jwt_required()
def get_email(email_id):
    require_staff()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, sender, subject, body, attachments, bl_numbers, created_at
        FROM customer_emails WHERE id = %s
    """, (email_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        abort(404, description='Email not found')
    email = {
        'id': row[0],
        'sender': row[1],
        'subject': row[2],
        'body': row[3],
        'attachments': row[4],
        'bl_numbers': row[5],
        'created_at': row[6],
        'replies': []
    }
    cur.execute("""
        SELECT id, sender, body, created_at
        FROM customer_email_replies WHERE customer_email_id = %s ORDER BY created_at ASC
    """, (email_id,))
    email['replies'] = [
        {'id': r[0], 'sender': r[1], 'body': r[2], 'created_at': r[3]} for r in cur.fetchall()
    ]
    cur.close()
    conn.close()
    logging.debug(f"[GET EMAIL] Email {email_id} with {len(email['replies'])} replies fetched")
    return jsonify(email)

@email_routes.route('/<int:email_id>/reply', methods=['POST'])
@jwt_required()
def reply_email(email_id):
    require_staff()
    data = request.get_json()
    reply_body = data.get('body')
    staff_sender = get_jwt_identity() if isinstance(get_jwt_identity(), str) else get_jwt_identity().get('email', 'staff')
    conn = get_db_conn()
    cur = conn.cursor()
    # Get original email info for sending
    cur.execute("SELECT sender, subject FROM customer_emails WHERE id = %s", (email_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        abort(404, description='Email not found')
    customer_email, orig_subject = row
    # Save reply
    cur.execute("""
        INSERT INTO customer_email_replies (customer_email_id, sender, body)
        VALUES (%s, %s, %s) RETURNING id, created_at
    """, (email_id, staff_sender, reply_body))
    reply_id, created_at = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    logging.debug(f"[REPLY] Reply {reply_id} saved for email {email_id}")
    # Send email to customer
    subject = f"Re: {orig_subject}" if orig_subject else "Reply from Logistics Company"
    send_ok = send_simple_email(customer_email, subject, reply_body)
    logging.debug(f"[REPLY] Email send status: {send_ok} to {customer_email}")
    return jsonify({'id': reply_id, 'created_at': created_at, 'email_sent': send_ok}), 201

@email_routes.route('/sent', methods=['GET'])
@jwt_required()
def sent_replies():
    require_staff()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, customer_email_id, sender, body, created_at
        FROM customer_email_replies ORDER BY created_at DESC LIMIT 100
    """)
    replies = [
        {'id': r[0], 'customer_email_id': r[1], 'sender': r[2], 'body': r[3], 'created_at': r[4]} for r in cur.fetchall()
    ]
    cur.close()
    conn.close()
    logging.debug(f"[SENT] {len(replies)} sent replies fetched")
    return jsonify(replies)
