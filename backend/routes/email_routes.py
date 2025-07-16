import os
import json
import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from config import get_db_conn
from email_utils import send_email

email_routes = Blueprint('email_routes', __name__)

@email_routes.route('/inbox', methods=['GET'])
@jwt_required()
def get_customer_emails():
    print("[DEBUG] Fetching all customer emails")
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, sender, subject, created_at, bl_numbers FROM customer_emails ORDER BY created_at DESC")
    rows = cursor.fetchall()
    emails = [
        {
            'id': row[0],
            'sender': row[1],
            'subject': row[2],
            'created_at': row[3],
            'bl_numbers': row[4]
        } for row in rows
    ]
    cursor.close()
    conn.close()
    return jsonify(emails)

@email_routes.route('/<int:email_id>', methods=['GET'])
@jwt_required()
def get_email_detail(email_id):
    print(f"[DEBUG] Fetching detail for email_id={email_id}")
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, sender, subject, body, attachments, bl_numbers, created_at FROM customer_emails WHERE id = %s", (email_id,))
    email_row = cursor.fetchone()
    if not email_row:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Email not found'}), 404
    cursor.execute("SELECT id, sender, body, created_at FROM customer_email_replies WHERE customer_email_id = %s ORDER BY created_at ASC", (email_id,))
    replies = [
        {
            'id': r[0],
            'sender': r[1],
            'body': r[2],
            'created_at': r[3]
        } for r in cursor.fetchall()
    ]
    email_detail = {
        'id': email_row[0],
        'sender': email_row[1],
        'subject': email_row[2],
        'body': email_row[3],
        'attachments': email_row[4] if email_row[4] else [],
        'bl_numbers': email_row[5],
        'created_at': email_row[6],
        'replies': replies
    }
    cursor.close()
    conn.close()
    return jsonify(email_detail)

@email_routes.route('/<int:email_id>/reply', methods=['POST'])
@jwt_required()
def reply_to_customer(email_id):
    data = request.json
    reply_body = data.get('body')
    print(f"[DEBUG] Replying to email_id={email_id}")
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT sender, subject FROM customer_emails WHERE id = %s", (email_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Email not found'}), 404
    to_email = row[0]
    subject = f"Re: {row[1]}"
    smtp_host = os.environ.get('EMAIL_HOST')
    smtp_port = int(os.environ.get('EMAIL_PORT', 587))
    smtp_user = os.environ.get('EMAIL_USERNAME')
    smtp_password = os.environ.get('EMAIL_PASSWORD')
    try:
        send_email(to_email, subject, reply_body, smtp_host, smtp_port, smtp_user, smtp_password)
        print(f"[DEBUG] Sent reply to {to_email}")
        cursor.execute("INSERT INTO customer_email_replies (customer_email_id, sender, body, created_at) VALUES (%s, %s, %s, %s)", (email_id, smtp_user, reply_body, datetime.datetime.now()))
        conn.commit()
        print(f"[DEBUG] Saved reply to DB for email_id={email_id}")
    except Exception as e:
        print(f"[ERROR] Failed to send reply: {e}")
        cursor.close()
        conn.close()
        return jsonify({'error': 'Failed to send reply'}), 500
    cursor.close()
    conn.close()
    return jsonify({'message': 'Reply sent and saved'})
