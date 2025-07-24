import os
import json
import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from config import get_db_conn
from email_utils import send_email
from email_utils import send_email_with_attachment
import requests

email_routes = Blueprint('email_routes', __name__)

@email_routes.route('/inbox', methods=['GET'])
@jwt_required()
def get_customer_emails():
    print('[DEBUG] /admin/email/inbox called - fetching emails from database only (no IMAP ingestion triggered). To fetch new emails, run the ingestion process manually or via admin endpoint.')
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
    send_email(to_email, subject, reply_body)
    print(f"[DEBUG] Sent reply to {to_email}")
    from config import EmailConfig
    try:
        cursor.execute("INSERT INTO customer_email_replies (customer_email_id, sender, body, created_at) VALUES (%s, %s, %s, %s)", (email_id, EmailConfig.FROM_EMAIL, reply_body, datetime.datetime.now()))
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

@email_routes.route('/draft_replies', methods=['GET'])
@jwt_required()
def get_draft_replies():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.id, r.customer_email_id, r.sender, r.body, r.created_at, e.subject, e.sender as customer_sender
        FROM customer_email_replies r
        JOIN customer_emails e ON r.customer_email_id = e.id
        WHERE r.is_draft = TRUE
        ORDER BY r.created_at DESC
    """)
    rows = cursor.fetchall()
    drafts = [
        {
            'id': row[0],
            'customer_email_id': row[1],
            'sender': row[2],
            'body': row[3],
            'created_at': row[4],
            'subject': row[5],
            'customer_sender': row[6]
        } for row in rows
    ]
    cursor.close()
    conn.close()
    return jsonify(drafts)

@email_routes.route('/email_replies/<int:reply_id>/send', methods=['POST'])
@jwt_required()
def send_draft_reply(reply_id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT customer_email_id, body FROM customer_email_replies WHERE id = %s AND is_draft = TRUE", (reply_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Draft not found'}), 404
    customer_email_id, body = row
    cursor.execute("SELECT sender, subject, attachments FROM customer_emails WHERE id = %s", (customer_email_id,))
    email_row = cursor.fetchone()
    if not email_row:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Customer email not found'}), 404
    to_email, subject, attachments_json = email_row
    attachments = []
    if attachments_json:
        import json
        links = json.loads(attachments_json)
        for link in links:
            local_path = f"/tmp/{os.path.basename(link)}"
            r = requests.get(link)
            with open(local_path, 'wb') as f:
                f.write(r.content)
            attachments.append(local_path)
    send_email_with_attachment(to_email, f"Re: {subject}", body, attachments)
    cursor.execute("UPDATE customer_email_replies SET is_draft = FALSE WHERE id = %s", (reply_id,))
    conn.commit()
    cursor.close()
    conn.close()
    for f in attachments:
        try:
            os.remove(f)
        except Exception:
            pass
    return jsonify({'message': 'Draft sent and marked as sent'})

@email_routes.route('/unprocessed_for_payments', methods=['GET'])
@jwt_required()
def get_unprocessed_for_payments():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, sender, subject, created_at, bl_numbers FROM customer_emails WHERE processed_for_payments=FALSE ORDER BY created_at DESC")
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
