

from flask import Blueprint, request, jsonify, send_from_directory
import json
import os
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.security import decrypt_sensitive_data
from config import get_db_conn  # Updated import
# Removed duplicate email processing system - using main email_ingestor.py instead

admin_routes = Blueprint('admin_routes', __name__)

@admin_routes.route('/admin/ingest-emails', methods=['POST'])
@jwt_required()
def admin_ingest_emails():
    from flask import request
    user = json.loads(get_jwt_identity())
    if user.get('username') != 'ray40':
        return jsonify({'error': 'Admins only!'}), 403
    
    # Use the main email processing system with FCM notifications
    from email_ingestor_working import process_inbox
    result = process_inbox(user_id=user.get('username'))
    return jsonify({'result': result})

@admin_routes.route('/admin/email-processing-status', methods=['GET'])
@jwt_required()
def get_email_processing_status():
    """Get current email processing status"""
    from email_ingestor_working import get_db_processing_status
    status = get_db_processing_status()
    return jsonify(status)

@admin_routes.route('/admin/email-ingest-errors', methods=['GET'])
@jwt_required()
def get_email_ingest_errors():
    user = json.loads(get_jwt_identity())
    if user.get('username') != 'ray40':
        return jsonify({'error': 'Admins only!'}), 403

    conn = get_db_conn()
    cur = conn.cursor()
    
    # Get email processing errors and issues
    errors = []
    
    # Check for emails with processing issues
    cur.execute("""
        SELECT id, sender, subject, created_at, 
               CASE 
                   WHEN bl_numbers IS NULL OR bl_numbers = '{}' THEN 'No BL numbers extracted'
                   WHEN processed_for_payments = FALSE THEN 'Not processed for payments'
                   ELSE 'Processing completed'
               END as status
        FROM customer_emails 
        WHERE (bl_numbers IS NULL OR bl_numbers = '{}' OR processed_for_payments = FALSE)
        ORDER BY created_at DESC 
        LIMIT 50
    """)
    
    for row in cur.fetchall():
        errors.append({
            'id': row[0],
            'filename': f"Email from {row[1]}",
            'reason': row[4],
            'raw_text': f"Subject: {row[2]}",
            'created_at': str(row[3])
        })
    
    # Check for duplicate payment issues
    cur.execute("""
        SELECT id, date, description, amount, reason, created_at, raw_text
        FROM unmatched_receipts 
        WHERE reason LIKE '%Duplicate Payment%'
        ORDER BY created_at DESC 
        LIMIT 20
    """)
    
    for row in cur.fetchall():
        errors.append({
            'id': f"DP_{row[0]}",
            'filename': row[2],
            'reason': row[4],
            'raw_text': row[6],
            'created_at': str(row[5])
        })
    
    cur.close()
    conn.close()
    return jsonify(errors)

@admin_routes.route('/admin/unmatched-receipts', methods=['GET'])
@jwt_required()
def get_unmatched_receipts():
    user = json.loads(get_jwt_identity())
    if user.get('username') != 'ray40':
        return jsonify({'error': 'Admins only!'}), 403

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, date, description, amount, reason, created_at, raw_text FROM unmatched_receipts ORDER BY created_at DESC")
    receipts = []
    for row in cur.fetchall():
        receipts.append({
            'id': row[0],
            'date': row[1],
            'description': row[2],
            'amount': row[3],
            'reason': row[4],
            'created_at': str(row[5]),
            'raw_text': row[6]
        })
    cur.close()
    conn.close()
    return jsonify(receipts)

# Admin-only endpoints

@admin_routes.route('/admin/users', methods=['GET'])
@jwt_required()
def get_users():
    user = json.loads(get_jwt_identity())
    if user.get('username') != 'ray40':
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
    if user.get('username') != 'ray40':
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
    if user.get('username') != 'ray40':
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

@admin_routes.route('/admin/canned-responses', methods=['GET'])
@jwt_required()
def get_canned_responses():
    try:
        # Assuming the file is in the backend directory
        return send_from_directory('.', 'canned_responses.json')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_routes.route('/admin/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload a file for email attachments"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file size (limit to 10MB)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return jsonify({'error': 'File too large. Maximum size is 10MB'}), 400
        
        # Check file type
        allowed_extensions = {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.jpg', '.jpeg', '.png'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}'}), 400
        
        # Save to temporary file and upload to Cloudinary
        import tempfile
        from cloudinary_utils import upload_filepath_to_cloudinary
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            file.save(tmp.name)
            local_path = tmp.name
        
        # Upload to Cloudinary
        cloud_url = upload_filepath_to_cloudinary(local_path, folder="email_attachments")
        
        # Clean up temporary file
        try:
            os.unlink(local_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'url': cloud_url,
            'filename': file.filename
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@admin_routes.route('/process-emails-without-replies', methods=['POST'])
@jwt_required()
def process_emails_without_replies():
    """Process all emails that don't have replies"""
    try:
        from email_ingestor_working import process_all_emails_without_replies
        
        processed_count = process_all_emails_without_replies()
        
        return jsonify({
            'success': True,
            'processed_count': processed_count,
            'message': f'Successfully processed {processed_count} emails without replies'
        })
        
    except Exception as e:
        logger.error(f"Error processing emails without replies: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
