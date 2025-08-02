#!/usr/bin/env python3
"""
Outlook Add-in API Endpoints
Backend integration for Microsoft Outlook add-in
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import logging
from config import get_db_conn
from email_ingestor import handle_email_via_openai, save_draft_reply
from utils.timezone_utils import get_hk_now, get_hk_now_iso

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint for Outlook API
outlook_api = Blueprint('outlook_api', __name__)

@outlook_api.route('/api/outlook/process-email', methods=['POST'])
def process_email_outlook():
    """Process email from Outlook add-in using existing email_ingestor logic"""
    try:
        data = request.get_json()
        
        # Extract email data from Outlook
        email_data = {
            'subject': data.get('subject', ''),
            'body': data.get('body', ''),
            'from_addr': data.get('from', ''),
            'outlook_message_id': data.get('messageId', ''),
            'outlook_user_id': data.get('userId', ''),
            'attachments': data.get('attachments', [])
        }
        
        logger.info(f"[Outlook] Processing email from {email_data['from_addr']}: {email_data['subject']}")
        
        # Store email in database first
        conn = get_db_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO customer_emails 
            (subject, body, from_addr, outlook_message_id, outlook_user_id, attachments, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            email_data['subject'],
            email_data['body'],
            email_data['from_addr'],
            email_data['outlook_message_id'],
            email_data['outlook_user_id'],
            json.dumps(email_data['attachments']),
            get_hk_now()
        ))
        
        email_id = cursor.fetchone()[0]
        conn.commit()
        
        # Process with existing AI logic from email_ingestor
        try:
            # Use the existing handle_email_via_openai function
            processing_result = handle_email_via_openai(
                email_data['subject'],
                email_data['body'],
                email_data['attachments'],
                email_data['from_addr']
            )
            
            # Mark as processed
            cursor.execute("""
                UPDATE customer_emails 
                SET openai_processed = TRUE, processed_at = %s
                WHERE id = %s
            """, (get_hk_now(), email_id))
            conn.commit()
            
            logger.info(f"[Outlook] Email {email_id} processed successfully with AI")
            
        except Exception as ai_error:
            logger.error(f"[Outlook] AI processing failed for email {email_id}: {ai_error}")
            # Still mark as processed but with error
            cursor.execute("""
                UPDATE customer_emails 
                SET openai_processed = TRUE, processed_at = %s, classification = 'error'
                WHERE id = %s
            """, (get_hk_now(), email_id))
            conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Email processed successfully with AI',
            'data': {
                'email_id': email_id,
                'status': 'processed',
                'ai_draft_created': True
            }
        })
        
    except Exception as e:
        logger.error(f"[Outlook] Error processing email: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing email: {str(e)}'
        }), 500

@outlook_api.route('/api/outlook/fetch-drafts', methods=['GET'])
def fetch_drafts_outlook():
    """Fetch AI-generated drafts for Outlook from customer_email_replies table"""
    try:
        user_id = request.args.get('userId', '')
        limit = int(request.args.get('limit', 10))
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Fetch recent AI drafts from customer_email_replies table
        cursor.execute("""
            SELECT 
                cer.id as reply_id,
                cer.customer_email_id,
                ce.subject,
                ce.from_addr,
                ce.created_at as email_date,
                cer.created_at as draft_date,
                cer.body as draft_content,
                cer.confidence_score,
                cer.is_draft,
                ce.outlook_user_id
            FROM customer_email_replies cer
            JOIN customer_emails ce ON cer.customer_email_id = ce.id
            WHERE cer.sender = 'openai_draft'
            AND cer.is_draft = TRUE
            AND (ce.outlook_user_id = %s OR %s = '')
            ORDER BY cer.created_at DESC
            LIMIT %s
        """, (user_id, user_id, limit))
        
        drafts = []
        for row in cursor.fetchall():
            drafts.append({
                'reply_id': row[0],
                'email_id': row[1],
                'subject': row[2],
                'from_addr': row[3],
                'email_date': row[4].isoformat() if row[4] else None,
                'draft_date': row[5].isoformat() if row[5] else None,
                'draft_content': row[6],
                'confidence_score': row[7],
                'is_draft': row[8],
                'outlook_user_id': row[9]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': drafts
        })
        
    except Exception as e:
        logger.error(f"[Outlook] Error fetching drafts: {e}")
        return jsonify({
            'success': False,
            'message': f'Error fetching drafts: {str(e)}'
        }), 500

@outlook_api.route('/api/outlook/get-draft-content', methods=['GET'])
def get_draft_content():
    """Get specific draft content for an email"""
    try:
        reply_id = request.args.get('replyId')
        
        if not reply_id:
            return jsonify({
                'success': False,
                'message': 'Reply ID is required'
            }), 400
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get draft content from customer_email_replies table
        cursor.execute("""
            SELECT 
                cer.body as draft_content,
                cer.confidence_score,
                cer.confidence_reasoning,
                ce.subject,
                ce.body as original_email,
                ce.from_addr,
                ce.created_at
            FROM customer_email_replies cer
            JOIN customer_emails ce ON cer.customer_email_id = ce.id
            WHERE cer.id = %s
        """, (reply_id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({
                'success': False,
                'message': 'Draft not found'
            }), 404
        
        draft_data = {
            'draft_content': row[0],
            'confidence_score': row[1],
            'confidence_reasoning': json.loads(row[2]) if row[2] else None,
            'original_email': {
                'subject': row[3],
                'body': row[4],
                'from_addr': row[5],
                'created_at': row[6].isoformat() if row[6] else None
            }
        }
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': draft_data
        })
        
    except Exception as e:
        logger.error(f"[Outlook] Error getting draft content: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting draft content: {str(e)}'
        }), 500

@outlook_api.route('/api/outlook/send-draft', methods=['POST'])
def send_draft_outlook():
    """Mark draft as sent and update status"""
    try:
        data = request.get_json()
        
        reply_id = data.get('replyId')
        sent_by = data.get('sentBy', 'outlook_user')
        
        if not reply_id:
            return jsonify({
                'success': False,
                'message': 'Reply ID is required'
            }), 400
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get the draft details
        cursor.execute("""
            SELECT customer_email_id, body FROM customer_email_replies 
            WHERE id = %s
        """, (reply_id,))
        
        row = cursor.fetchone()
        if not row:
            return jsonify({
                'success': False,
                'message': 'Draft not found'
            }), 404
        
        customer_email_id = row[0]
        draft_content = row[1]
        
        # Mark draft as sent (not a draft anymore)
        cursor.execute("""
            UPDATE customer_email_replies 
            SET is_draft = FALSE, sent_at = %s, sent_by = %s
            WHERE id = %s
        """, (get_hk_now(), sent_by, reply_id))
        
        # Update email status
        cursor.execute("""
            UPDATE customer_emails 
            SET processed_for_payments = TRUE
            WHERE id = %s
        """, (customer_email_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Draft marked as sent successfully'
        })
        
    except Exception as e:
        logger.error(f"[Outlook] Error sending draft: {e}")
        return jsonify({
            'success': False,
            'message': f'Error sending draft: {str(e)}'
        }), 500

@outlook_api.route('/api/outlook/status', methods=['GET'])
def outlook_status():
    """Get system status for Outlook add-in"""
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute("SELECT COUNT(*) FROM customer_emails WHERE openai_processed = TRUE")
        processed_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM customer_email_replies WHERE is_draft = TRUE")
        draft_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM customer_email_replies WHERE is_draft = FALSE")
        sent_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'system_status': 'operational',
                'processed_emails': processed_count,
                'available_drafts': draft_count,
                'sent_replies': sent_count,
                'last_updated': get_hk_now_iso()
            }
        })
        
    except Exception as e:
        logger.error(f"[Outlook] Error getting status: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting status: {str(e)}'
        }), 500 