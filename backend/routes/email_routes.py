import os
import json
import datetime
import time
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import get_db_conn
from email_utils import send_email
from email_utils import send_email_with_attachment
import requests
import logging

logger = logging.getLogger(__name__)

email_routes = Blueprint('email_routes', __name__)

# Database-based storage for email locks and user activity
from config import get_db_conn

def get_user_id_from_token():
    """Extract user ID from JWT token"""
    try:
        identity = get_jwt_identity()
        if isinstance(identity, str):
            # Parse JSON string identity
            identity_data = json.loads(identity)
            user_id = identity_data.get('id')
        elif isinstance(identity, dict):
            # Direct dict identity
            user_id = identity.get('id')
        else:
            # Fallback: assume identity is the user ID directly
            user_id = identity
        
        # Ensure user_id is always a string
        return str(user_id) if user_id is not None else None
    except Exception as e:
        print(f"Error extracting user ID from token: {e}")
        return None

def check_email_lock(email_id, user_id):
    """Check if email is locked by another user"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Clean up expired locks first
        cursor.execute("SELECT cleanup_expired_email_editing_locks()")
        
        # Ensure user_id is a string
        user_id_str = str(user_id) if user_id is not None else None
        
        # Check for active lock
        cursor.execute("""
            SELECT user_id, created_at, expires_at
            FROM email_editing_locks
            WHERE email_id = %s AND expires_at > NOW()
        """, (email_id,))
        
        lock_row = cursor.fetchone()
        if lock_row:
            lock_user_id, created_at, expires_at = lock_row
            # Check if locked by different user
            if lock_user_id != user_id_str:
                return {
                    'user_id': lock_user_id,
                    'timestamp': created_at.timestamp() if created_at else time.time(),
                    'email_id': email_id
                }
        return False
        
    except Exception as e:
        print(f"Error checking email lock: {e}")
        return False
    finally:
        cursor.close()

def acquire_email_lock(email_id, user_id):
    """Acquire lock on email for editing"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Ensure user_id is a string
        user_id_str = str(user_id) if user_id is not None else None
        
        # Check if already locked
        lock_info = check_email_lock(email_id, user_id_str)
        if lock_info:
            return False, lock_info
        
        # Try to acquire lock (will fail if another lock exists due to UNIQUE constraint)
        cursor.execute("""
            INSERT INTO email_editing_locks (email_id, user_id, expires_at)
            VALUES (%s, %s, NOW() + INTERVAL '10 minutes')
            RETURNING id
        """, (email_id, user_id_str))
        
        lock_id = cursor.fetchone()
        if lock_id:
            conn.commit()
            return True, None
        else:
            return False, None
            
    except Exception as e:
        # Check if error is due to existing lock
        if "duplicate key" in str(e).lower():
            # Get the existing lock info
            lock_info = check_email_lock(email_id, user_id_str)
            return False, lock_info
        else:
            print(f"Error acquiring email lock: {e}")
            return False, None
    finally:
        cursor.close()
        conn.close()

def release_email_lock(email_id, user_id):
    """Release lock on email"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Ensure user_id is a string
        user_id_str = str(user_id) if user_id is not None else None
        
        cursor.execute("""
            DELETE FROM email_editing_locks 
            WHERE email_id = %s AND user_id = %s
        """, (email_id, user_id_str))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
        
    except Exception as e:
        print(f"Error releasing email lock: {e}")
        return False
    finally:
        cursor.close()

def update_user_activity(user_id, email_id=None, action=None):
    """Update user activity tracking"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Ensure user_id is a string
        user_id_str = str(user_id) if user_id is not None else None
        
        cursor.execute("""
            INSERT INTO user_activity (user_id, current_email_id, current_action, last_activity)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (user_id) DO UPDATE SET
                current_email_id = EXCLUDED.current_email_id,
                current_action = EXCLUDED.current_action,
                last_activity = NOW()
        """, (user_id_str, email_id, action))
        
        conn.commit()
        
    except Exception as e:
        print(f"Error updating user activity: {e}")
    finally:
        cursor.close()
        conn.close()

@email_routes.route('/inbox', methods=['GET'])
@jwt_required()
def get_customer_emails():
    """
    Get paginated customer emails with performance optimizations.
    Supports filtering and pagination for better performance with large datasets.
    """
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)  # 50 emails per page for better performance
    offset = (page - 1) * per_page
    
    # Get filter parameters
    sender_filter = request.args.get('sender', '')
    subject_filter = request.args.get('subject', '')
    bl_number_filter = request.args.get('bl_number', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    reply_status = request.args.get('reply_status', 'all')
    

    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Build WHERE clause for filtering
        where_conditions = []
        params = []
        
        if sender_filter:
            where_conditions.append("sender ILIKE %s")
            params.append(f'%{sender_filter}%')
        
        if subject_filter:
            where_conditions.append("subject ILIKE %s")
            params.append(f'%{subject_filter}%')
        
        if bl_number_filter:
            where_conditions.append("(EXISTS(SELECT 1 FROM unnest(bl_numbers) AS bl WHERE bl ILIKE %s) OR subject ILIKE %s OR body ILIKE %s)")
            params.extend([f'%{bl_number_filter}%', f'%{bl_number_filter}%', f'%{bl_number_filter}%'])
        
        if date_from:
            where_conditions.append("created_at >= %s")
            params.append(date_from)
        
        if date_to:
            where_conditions.append("created_at <= %s")
            params.append(date_to)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        # Get total count for pagination - use index if no filters
        if not where_conditions:
            # No filters - use fast count
            cursor.execute("SELECT COUNT(*) FROM customer_emails")
            total = cursor.fetchone()[0]
        else:
            # Has filters - use filtered count
            count_query = f"SELECT COUNT(*) FROM customer_emails WHERE {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
        
        # Get paginated emails - optimized for remote database
        if not where_conditions:
            # No filters - use simple query with index
            email_query = """
                SELECT 
                    e.id, 
                    e.sender, 
                    e.subject, 
                    e.created_at, 
                    e.bl_numbers
                FROM customer_emails e
                ORDER BY e.created_at DESC, e.id DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(email_query, [per_page, offset])
        else:
            # Has filters - use filtered query
            email_query = f"""
                SELECT 
                    e.id, 
                    e.sender, 
                    e.subject, 
                    e.created_at, 
                    e.bl_numbers
                FROM customer_emails e
                WHERE {where_clause}
                ORDER BY e.created_at DESC, e.id DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(email_query, params + [per_page, offset])
        rows = cursor.fetchall()
        
        emails = [
            {
                'id': row[0],
                'sender': row[1],
                'subject': row[2],
                'created_at': row[3],
                'bl_numbers': row[4],
                'has_replies': False,  # Will be updated in separate query
                'reply_count': 0
            } for row in rows
        ]
        
        # Get reply counts and sent status in a separate query (more efficient for remote DB)
        if emails:
            email_ids = [str(email['id']) for email in emails]
            placeholders = ','.join(['%s'] * len(email_ids))
            cursor.execute(f"""
                SELECT 
                    customer_email_id, 
                    COUNT(*) as reply_count,
                    COUNT(CASE WHEN sent_at IS NOT NULL THEN 1 END) as sent_count
                FROM customer_email_replies 
                WHERE customer_email_id IN ({placeholders})
                GROUP BY customer_email_id
            """, email_ids)
            reply_data = dict((row[0], {'count': row[1], 'sent': row[2]}) for row in cursor.fetchall())
            
            # Update emails with reply counts and sent status
            for email in emails:
                data = reply_data.get(email['id'], {'count': 0, 'sent': 0})
                email['reply_count'] = data['count']
                email['sent_count'] = data['sent']
                email['has_replies'] = data['count'] > 0
                email['has_sent_replies'] = data['sent'] > 0
        
        # Apply reply status filter if needed
        print(f"DEBUG: reply_status parameter = '{reply_status}'")
        print(f"DEBUG: Total emails before filter: {len(emails)}")
        
        # Show sample of emails before filtering
        if emails:
            print(f"DEBUG: Sample emails before filter:")
            for i, email in enumerate(emails[:3]):
                print(f"  {i+1}. ID {email['id']}: has_replies={email['has_replies']}, has_sent_replies={email['has_sent_replies']}")
        
        if reply_status == 'sent':
            emails = [e for e in emails if e['has_sent_replies']]
            print(f"DEBUG: 'sent' filter applied, showing {len(emails)} emails")
        elif reply_status == 'ai_ready':
            # FIXED: Corrected logic - AI Reply Ready shows emails with replies but no sent replies
            emails = [e for e in emails if e['has_replies'] and not e['has_sent_replies']]
            print(f"DEBUG: 'ai_ready' filter applied, showing {len(emails)} emails")
        elif reply_status == 'no_reply':
            # FIXED: Corrected logic - No AI Reply shows emails with no replies at all
            emails = [e for e in emails if not e['has_replies']]
            print(f"DEBUG: 'no_reply' filter applied, showing {len(emails)} emails")
        
        # Additional debugging: show what each email's status should be
        if emails and reply_status in ['ai_ready', 'no_reply']:
            print(f"DEBUG: Emails returned for '{reply_status}' filter:")
            for i, email in enumerate(emails[:5]):  # Show first 5 emails
                expected_status = "AI Reply Ready" if email['has_replies'] and not email['has_sent_replies'] else "No AI Reply" if not email['has_replies'] else "Sent"
                print(f"  {i+1}. ID {email['id']}: has_replies={email['has_replies']}, has_sent_replies={email['has_sent_replies']} → Should show: {expected_status}")
        else:
            print(f"DEBUG: No filter applied (reply_status='{reply_status}'), showing {len(emails)} emails")
        
        # Show sample of filtered emails
        if emails:
            print(f"DEBUG: Sample filtered emails:")
            for i, email in enumerate(emails[:3]):
                print(f"  {i+1}. ID {email['id']}: has_replies={email['has_replies']}, has_sent_replies={email['has_sent_replies']}")
        
        return jsonify({
            'emails': emails,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
            'has_more': page < (total + per_page - 1) // per_page
        })
        
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return jsonify({'error': 'Failed to fetch emails'}), 500
    finally:
        cursor.close()
        conn.close()

@email_routes.route('/<int:email_id>', methods=['GET'])
@jwt_required()
def get_email_detail(email_id):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, sender, subject, body, attachments, bl_numbers, created_at FROM customer_emails WHERE id = %s", (email_id,))
    email_row = cursor.fetchone()
    if not email_row:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Email not found'}), 404
    
    # Process attachments
    attachments_raw = email_row[4]
    
    # Process attachments - simple and reliable approach
    attachments = []
    if attachments_raw:
        if isinstance(attachments_raw, list):
            # Already a list
            attachments = attachments_raw
        elif isinstance(attachments_raw, str):
            # Try to parse as JSON
            try:
                import json
                parsed = json.loads(attachments_raw)
                if isinstance(parsed, list):
                    attachments = parsed
                else:
                    attachments = [parsed]
            except json.JSONDecodeError:
                # If not valid JSON, treat as single attachment
                attachments = [attachments_raw]
        else:
            # Convert to string and treat as single attachment
            attachments = [str(attachments_raw)]
    

    
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
        'attachments': attachments,
        'bl_numbers': email_row[5],
        'created_at': email_row[6],
        'replies': replies
    }

    cursor.close()
    conn.close()
    return jsonify(email_detail)

@email_routes.route('/<int:email_id>/reply', methods=['POST'])
@jwt_required()
def reply_to_email(email_id):
    """Send a reply to a customer email"""
    try:
        data = request.get_json()
        reply_body = data.get('body', '').strip()
        attachments = data.get('attachments', [])  # List of file URLs
        
        if not reply_body:
            return jsonify({'error': 'Reply body is required'}), 400
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Check if email exists and get current status
        cursor.execute("""
            SELECT ce.id, ce.sender, ce.subject, ce.body,
                   COUNT(cer.id) as reply_count,
                   MAX(cer.created_at) as last_reply_time
            FROM customer_emails ce
            LEFT JOIN customer_email_replies cer ON ce.id = cer.customer_email_id
            WHERE ce.id = %s
            GROUP BY ce.id, ce.sender, ce.subject, ce.body
        """, (email_id,))
        
        email_data = cursor.fetchone()
        if not email_data:
            return jsonify({'error': 'Email not found'}), 404
        
        email_id, sender, subject, body, reply_count, last_reply_time = email_data
        
        # Check if this is a duplicate reply (within 5 minutes)
        if last_reply_time:
            from datetime import datetime, timedelta
            time_diff = datetime.now() - last_reply_time
            if time_diff < timedelta(minutes=5):
                return jsonify({
                    'error': 'This email has been replied to recently. Please refresh to see the latest status.',
                    'last_reply_time': last_reply_time.isoformat()
                }), 409
        
        # Send the email
        try:
            # Use the existing email sending logic
            from email_utils import send_email_with_attachment
            import requests
            import tempfile
            import os
            
            # Download attachments to temporary files
            temp_attachments = []
            for url in attachments:
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    
                    # Create temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(url)[1]) as tmp:
                        tmp.write(response.content)
                        temp_attachments.append(tmp.name)
                except Exception as e:
                    logger.error(f"Failed to download attachment {url}: {e}")
                    continue
            
            success = send_email_with_attachment(
                to=sender,
                subject=f"Re: {subject}",
                body=reply_body,
                attachments=temp_attachments
            )
            
            # Clean up temporary files
            for temp_file in temp_attachments:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            if not success:
                return jsonify({'error': 'Failed to send email'}), 500
                
        except Exception as e:
            logger.error(f"Error sending email reply: {e}")
            return jsonify({'error': f'Failed to send email: {str(e)}'}), 500
        
        # Save the reply to database
        cursor.execute("""
            INSERT INTO customer_email_replies (
                customer_email_id, sender, body, created_at, is_draft, auto_sent
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            email_id,
            'support@iqstrade.com',  # or get from config
            reply_body,
            datetime.now(),
            False,  # Not a draft since we're sending it
            True    # Auto-sent
        ))
        
        reply_id = cursor.fetchone()[0] if cursor.description else None
        
        # Update email status to indicate it has been replied to
        cursor.execute("""
            UPDATE customer_emails 
            SET status = 'Replied', updated_at = %s
            WHERE id = %s
        """, (datetime.now(), email_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully sent reply to email {email_id}")
        
        return jsonify({
            'success': True,
            'message': 'Reply sent successfully',
            'reply_id': reply_id
        })
        
    except Exception as e:
        logger.error(f"Error in reply_to_email: {e}")
        return jsonify({'error': str(e)}), 500

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

@email_routes.route('/processor/status', methods=['GET'])
@jwt_required()
def get_email_processor_status():
    """Get email processor status"""
    try:
        from email_processor import get_email_processor_status
        status = get_email_processor_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@email_routes.route('/processor/force', methods=['POST'])
@jwt_required()
def force_email_processing():
    """Force immediate email processing"""
    try:
        from email_processor import force_email_processing
        result = force_email_processing()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@email_routes.route('/processor/pause', methods=['POST'])
@jwt_required()
def pause_email_processor():
    """Pause background email processing"""
    try:
        from email_processor import pause_email_processor
        pause_email_processor()
        return jsonify({'status': 'success', 'message': 'Background email processing paused'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@email_routes.route('/processor/resume', methods=['POST'])
@jwt_required()
def resume_email_processor():
    """Resume background email processing"""
    try:
        from email_processor import resume_email_processor
        resume_email_processor()
        return jsonify({'status': 'success', 'message': 'Background email processing resumed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@email_routes.route('/processor/stop', methods=['POST'])
@jwt_required()
def stop_email_processor():
    """Stop background email processing"""
    try:
        from email_processor import stop_email_processor
        stop_email_processor()
        return jsonify({'status': 'success', 'message': 'Background email processing stopped'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@email_routes.route('/count', methods=['GET'])
@jwt_required()
def get_email_count():
    """Get total email count for caching"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        total = cursor.fetchone()[0]
        return jsonify({'total': total})
    except Exception as e:
        print(f"Error getting email count: {e}")
        return jsonify({'error': 'Failed to get email count'}), 500
    finally:
        cursor.close()
        conn.close()

@email_routes.route('/<int:email_id>/lock', methods=['POST'])
@jwt_required()
def lock_email(email_id):
    """Acquire lock on email for editing"""
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    success, lock_info = acquire_email_lock(email_id, user_id)
    if success:
        update_user_activity(user_id, email_id, 'editing')
        return jsonify({'message': 'Email locked successfully', 'locked': True})
    else:
        # Check if lock_info is a dictionary (existing lock) or False (no lock info)
        if lock_info and isinstance(lock_info, dict):
            return jsonify({
                'error': 'Email is locked by another user',
                'locked': False,
                'locked_by': lock_info['user_id'],
                'locked_since': lock_info['timestamp']
            }), 409
        else:
            return jsonify({
                'error': 'Failed to acquire email lock',
                'locked': False
            }), 400

@email_routes.route('/<int:email_id>/unlock', methods=['POST'])
@jwt_required()
def unlock_email(email_id):
    """Release lock on email"""
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    success = release_email_lock(email_id, user_id)
    if success:
        update_user_activity(user_id, None, None)
        return jsonify({'message': 'Email unlocked successfully'})
    else:
        # If lock doesn't exist or doesn't belong to user, consider it "unlocked"
        update_user_activity(user_id, None, None)
        return jsonify({'message': 'Email unlocked successfully (no lock found)'})

@email_routes.route('/<int:email_id>/lock/status', methods=['GET'])
@jwt_required()
def get_email_lock_status(email_id):
    """Get current lock status of email"""
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    lock_info = check_email_lock(email_id, user_id)
    if lock_info:
        return jsonify({
            'locked': True,
            'locked_by': lock_info['user_id'],
            'locked_since': lock_info['timestamp'],
            'locked_by_me': lock_info['user_id'] == user_id
        })
    else:
        return jsonify({'locked': False})

@email_routes.route('/activity', methods=['GET'])
@jwt_required()
def get_user_activity():
    """Get current user activity across all users"""
    current_user_id = get_user_id_from_token()
    if not current_user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Clean up stale activity
        cursor.execute("SELECT cleanup_stale_user_activity()")
        
        # Get all active users
        cursor.execute("""
            SELECT user_id, current_email_id, current_action, last_activity
            FROM user_activity
            WHERE last_activity > NOW() - INTERVAL '30 minutes'
        """)
        
        active_users = {}
        for row in cursor.fetchall():
            user_id, email_id, action, last_activity = row
            active_users[user_id] = {
                'last_activity': last_activity.timestamp() if last_activity else time.time(),
                'current_email_id': email_id,
                'current_action': action,
                'is_online': True
            }
        
        # Get current email locks
        cursor.execute("""
            SELECT email_id, user_id, created_at, expires_at
            FROM email_editing_locks
            WHERE expires_at > NOW()
        """)
        
        email_locks = {}
        for row in cursor.fetchall():
            email_id, user_id, created_at, expires_at = row
            email_locks[email_id] = {
                'user_id': user_id,
                'timestamp': created_at.timestamp() if created_at else time.time(),
                'email_id': email_id
            }
        
        return jsonify({
            'current_user_id': current_user_id,
            'active_users': active_users,
            'email_locks': email_locks
        })
        
    except Exception as e:
        print(f"Error getting user activity: {e}")
        return jsonify({'error': 'Failed to get user activity'}), 500
    finally:
        cursor.close()
        conn.close()

@email_routes.route('/<int:email_id>/activity', methods=['GET'])
@jwt_required()
def get_email_activity(email_id):
    """Get activity for specific email"""
    user_id = get_user_id_from_token()
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Find users currently working on this email
        cursor.execute("""
            SELECT user_id, current_action, last_activity
            FROM user_activity
            WHERE current_email_id = %s AND last_activity > NOW() - INTERVAL '30 minutes'
        """, (email_id,))
        
        users_on_email = []
        for row in cursor.fetchall():
            uid, action, last_activity = row
            users_on_email.append({
                'user_id': uid,
                'action': action,
                'last_activity': last_activity.timestamp() if last_activity else time.time()
            })
        
        # Get lock info
        lock_info = check_email_lock(email_id, user_id)
        
        return jsonify({
            'email_id': email_id,
            'users_working_on_email': users_on_email,
            'lock_info': lock_info,
            'locked_by_me': lock_info and lock_info['user_id'] == user_id if lock_info else False
        })
        
    except Exception as e:
        print(f"Error getting email activity: {e}")
        return jsonify({'error': 'Failed to get email activity'}), 500
    finally:
        cursor.close()
        conn.close()

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

@email_routes.route('/<int:email_id>/force-unlock', methods=['POST'])
@jwt_required()
def force_unlock_email(email_id):
    """Force unlock an email regardless of who has the lock"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Delete any existing lock for this email
        cursor.execute("""
            DELETE FROM email_editing_locks
            WHERE email_id = %s
        """, (email_id,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Force unlocked email {email_id}, deleted {deleted_count} locks")
        
        return jsonify({
            'success': True,
            'message': f'Email {email_id} force unlocked successfully',
            'deleted_locks': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error force unlocking email {email_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_routes.route('/force-unlock-all', methods=['POST'])
@jwt_required()
def force_unlock_all_emails():
    """Force unlock all emails - emergency cleanup"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Delete all locks
        cursor.execute("DELETE FROM email_editing_locks")
        deleted_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Force unlocked all emails, deleted {deleted_count} locks")
        
        return jsonify({
            'success': True,
            'message': f'All emails force unlocked successfully',
            'deleted_locks': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error force unlocking all emails: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
