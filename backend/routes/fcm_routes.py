from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import pytz
from config import get_db_conn, return_db_conn
from fcm_service_fallback import fcm_service_fallback

fcm_routes = Blueprint('fcm_routes', __name__)

@fcm_routes.route('/fcm/test-simple', methods=['GET'])
def test_simple():
    """
    Simple test route to verify FCM blueprint is working
    """
    return jsonify({'message': 'FCM blueprint is working!'}), 200

@fcm_routes.route('/fcm/token/public', methods=['POST'])
def save_fcm_token_public():
    """
    Save FCM token for testing (no authentication required)
    """
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'FCM token is required'}), 400
        
        # Simple test - just return success without database operations
        return jsonify({'message': 'FCM token received successfully', 'token': token[:20] + '...'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error processing request: {str(e)}'}), 500

@fcm_routes.route('/fcm/token', methods=['POST'])
@jwt_required()
def save_fcm_token():
    """
    Save FCM token for the current user
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'FCM token is required'}), 400
        
        conn = get_db_conn()
        cur = conn.cursor()
        
        # Check if token already exists
        cur.execute('SELECT id FROM fcm_tokens WHERE token = %s', (token,))
        existing_token = cur.fetchone()
        
        if existing_token:
            # Update existing token
            cur.execute(
                'UPDATE fcm_tokens SET user_id = %s, updated_at = %s WHERE token = %s',
                (user_id, datetime.now(pytz.timezone('Asia/Hong_Kong')), token)
            )
        else:
            # Insert new token
            cur.execute(
                'INSERT INTO fcm_tokens (user_id, token, created_at, updated_at) VALUES (%s, %s, %s, %s)',
                (user_id, token, datetime.now(pytz.timezone('Asia/Hong_Kong')), datetime.now(pytz.timezone('Asia/Hong_Kong')))
            )
        
        conn.commit()
        cur.close()
        return_db_conn(conn)
        
        return jsonify({'message': 'FCM token saved successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error saving FCM token: {str(e)}'}), 500

@fcm_routes.route('/fcm/tokens', methods=['GET'])
@jwt_required()
def get_user_tokens():
    """
    Get FCM tokens for the current user
    """
    try:
        user_id = get_jwt_identity()
        
        conn = get_db_conn()
        cur = conn.cursor()
        
        cur.execute('SELECT token, created_at, updated_at FROM fcm_tokens WHERE user_id = %s', (user_id,))
        tokens = cur.fetchall()
        
        cur.close()
        return_db_conn(conn)
        
        token_list = [
            {
                'token': token[0],
                'created_at': token[1].isoformat() if token[1] else None,
                'updated_at': token[2].isoformat() if token[2] else None
            }
            for token in tokens
        ]
        
        return jsonify({'tokens': token_list}), 200
        
    except Exception as e:
        return jsonify({'error': f'Error fetching FCM tokens: {str(e)}'}), 500

@fcm_routes.route('/fcm/notify/new-bill', methods=['POST'])
@jwt_required()
def notify_new_bill():
    """
    Send notification for new bill upload
    """
    try:
        data = request.get_json()
        bill_id = data.get('bill_id')
        customer_name = data.get('customer_name')
        amount = data.get('amount')
        bill_number = data.get('bill_number')
        
        if not all([bill_id, customer_name, amount, bill_number]):
            return jsonify({'error': 'Missing required fields: bill_id, customer_name, amount, bill_number'}), 400
        
        result = fcm_service_fallback.send_to_topic(
            topic='new_bills',
            title='📄 New Bill Uploaded',
            body=f'Bill {bill_number} uploaded by {customer_name} - ${amount:.2f}',
            data={
                'type': 'new_bill',
                'bill_id': str(bill_id),
                'bill_number': bill_number,
                'customer_name': customer_name,
                'amount': str(amount),
                'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
            }
        )
        
        if result['success']:
            return jsonify({
                'message': 'New bill notification sent successfully',
                'result': result
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send notification',
                'result': result
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Error sending new bill notification: {str(e)}'}), 500

@fcm_routes.route('/fcm/notify/payment-confirmation', methods=['POST'])
@jwt_required()
def notify_payment_confirmation():
    """
    Send notification for payment confirmation
    """
    try:
        data = request.get_json()
        bill_id = data.get('bill_id')
        bill_number = data.get('bill_number')
        amount = data.get('amount')
        payment_method = data.get('payment_method', 'Unknown')
        
        if not all([bill_id, bill_number, amount]):
            return jsonify({'error': 'Missing required fields: bill_id, bill_number, amount'}), 400
        
        result = fcm_service_fallback.send_to_topic(
            topic='payment_confirmations',
            title='✅ Payment Confirmed',
            body=f'Payment received for Bill {bill_number} - ${amount:.2f}',
            data={
                'type': 'payment_confirmation',
                'bill_id': str(bill_id),
                'bill_number': bill_number,
                'amount': str(amount),
                'payment_method': payment_method,
                'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
            }
        )
        
        if result['success']:
            return jsonify({
                'message': 'Payment confirmation notification sent successfully',
                'result': result
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send notification',
                'result': result
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Error sending payment confirmation notification: {str(e)}'}), 500

@fcm_routes.route('/fcm/notify/system-error', methods=['POST'])
@jwt_required()
def notify_system_error():
    """
    Send notification for system errors
    """
    try:
        data = request.get_json()
        error_type = data.get('error_type')
        error_message = data.get('error_message')
        severity = data.get('severity', 'high')
        
        if not all([error_type, error_message]):
            return jsonify({'error': 'Missing required fields: error_type, error_message'}), 400
        
        result = fcm_service_fallback.send_to_topic(
            topic='system_alerts',
            title=f'🚨 System {error_type.title()}',
            body=f'{error_message}',
            data={
                'type': 'system_error',
                'error_type': error_type,
                'error_message': error_message,
                'severity': severity,
                'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
            }
        )
        
        if result['success']:
            return jsonify({
                'message': 'System error notification sent successfully',
                'result': result
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send notification',
                'result': result
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Error sending system error notification: {str(e)}'}), 500

@fcm_routes.route('/fcm/notify/customer-escalation', methods=['POST'])
@jwt_required()
def notify_customer_escalation():
    """
    Send notification for customer escalations
    """
    try:
        data = request.get_json()
        customer_name = data.get('customer_name')
        customer_phone = data.get('customer_phone')
        issue_type = data.get('issue_type')
        priority = data.get('priority', 'high')
        
        if not all([customer_name, customer_phone, issue_type]):
            return jsonify({'error': 'Missing required fields: customer_name, customer_phone, issue_type'}), 400
        
        result = fcm_service_fallback.send_to_topic(
            topic='customer_escalations',
            title=f'📞 Customer Escalation - {issue_type.title()}',
            body=f'{customer_name} ({customer_phone}) needs attention',
            data={
                'type': 'customer_escalation',
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'issue_type': issue_type,
                'priority': priority,
                'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
            }
        )
        
        if result['success']:
            return jsonify({
                'message': 'Customer escalation notification sent successfully',
                'result': result
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send notification',
                'result': result
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Error sending customer escalation notification: {str(e)}'}), 500

@fcm_routes.route('/fcm/notify/custom', methods=['POST'])
@jwt_required()
def send_custom_notification():
    """
    Send custom notification to a topic
    """
    try:
        data = request.get_json()
        topic = data.get('topic')
        title = data.get('title')
        body = data.get('body')
        custom_data = data.get('data', {})
        
        if not all([topic, title, body]):
            return jsonify({'error': 'Missing required fields: topic, title, body'}), 400
        
        result = fcm_service_fallback.send_to_topic(
            topic=topic,
            title=title,
            body=body,
            data=custom_data
        )
        
        if result['success']:
            return jsonify({
                'message': 'Custom notification sent successfully',
                'result': result
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send notification',
                'result': result
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Error sending custom notification: {str(e)}'}), 500

@fcm_routes.route('/fcm/subscribe', methods=['POST'])
def subscribe_to_topic():
    """
    Subscribe FCM token to a topic (no authentication required)
    Simplified to just save token to database
    """
    try:
        print('📱 Subscribe endpoint called')
        data = request.get_json()
        print(f'📱 Received data: {data}')
        
        token = data.get('token')
        topic = data.get('topic', 'test')
        
        print(f'📱 Token: {token[:20] if token else "None"}...')
        print(f'📱 Topic: {topic}')
        
        if not token:
            print('📱 Error: No token provided')
            return jsonify({'error': 'FCM token is required'}), 400
        
        print(f'📱 Saving FCM token to database: {token[:20]}...')
        
        # Save token to database
        conn = get_db_conn()
        cur = conn.cursor()
        
        # Check if token already exists
        cur.execute('SELECT id FROM fcm_tokens WHERE token = %s', (token,))
        existing = cur.fetchone()
        
        if existing:
            # Update existing token
            cur.execute('UPDATE fcm_tokens SET is_active = TRUE, updated_at = NOW() WHERE token = %s', (token,))
            print(f'📱 Updated existing FCM token')
        else:
            # Insert new token with NULL user_id (for public tokens)
            cur.execute('''
                INSERT INTO fcm_tokens (token, user_id, is_active, created_at, updated_at) 
                VALUES (%s, NULL, TRUE, NOW(), NOW())
            ''', (token,))
            print(f'📱 Inserted new FCM token with NULL user_id')
        
        conn.commit()
        cur.close()
        return_db_conn(conn)
        
        print(f'📱 Successfully saved token to database')
        
        return jsonify({
            'message': f'Successfully saved FCM token for topic: {topic}',
            'token': token[:20] + '...',
            'topic': topic
        }), 200
            
    except Exception as e:
        print('📱 Error saving FCM token:', str(e))
        import traceback
        print('📱 Full error traceback:')
        print(traceback.format_exc())
        return jsonify({'error': f'Error saving FCM token: {str(e)}'}), 500

@fcm_routes.route('/fcm/test/public', methods=['POST'])
def test_notification_public():
    """
    Send a test notification (no authentication required)
    """
    try:
        print('🧪 Sending test notification via FCM...')
        result = fcm_service_fallback.send_to_topic(
            topic='test',
            title='🧪 Test Notification',
            body='This is a test notification from IQS Trade system',
            data={'type': 'test', 'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()}
        )
        
        print('🧪 FCM result:', result)
        
        if result['success']:
            return jsonify({
                'message': 'Test notification sent successfully via FCM!',
                'result': result,
                'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send FCM notification',
                'result': result
            }), 500
            
    except Exception as e:
        print('🧪 Error sending FCM notification:', str(e))
        return jsonify({'error': f'Error sending FCM notification: {str(e)}'}), 500

@fcm_routes.route('/fcm/test', methods=['POST'])
@jwt_required()
def test_notification():
    """
    Send a test notification
    """
    try:
        result = fcm_service_fallback.send_to_topic(
            topic='test',
            title='🧪 Test Notification',
            body='This is a test notification from IQS Trade system',
            data={'type': 'test', 'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()}
        )
        
        if result['success']:
            return jsonify({
                'message': 'Test notification sent successfully',
                'result': result
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send test notification',
                'result': result
            }), 500
            
    except Exception as e:
        return jsonify({'error': f'Error sending test notification: {str(e)}'}), 500

@fcm_routes.route('/fcm/send/direct', methods=['POST'])
def send_direct_notification():
    """
    Send notification directly to a specific FCM token (no authentication required)
    """
    try:
        data = request.get_json()
        token = data.get('token')
        title = data.get('title', 'Direct Notification')
        body = data.get('body', 'This is a direct notification')
        
        if not token:
            return jsonify({'error': 'FCM token is required'}), 400
        
        print(f'📱 Sending direct notification to token: {token[:20]}...')
        result = fcm_service_fallback.send_notification(
            tokens=[token],
            title=title,
            body=body,
            data={'type': 'direct_test', 'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()}
        )
        
        if result['success']:
            return jsonify({
                'message': 'Direct notification sent successfully',
                'result': result
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send direct notification',
                'result': result
            }), 500
            
    except Exception as e:
        print('📱 Error sending direct notification:', str(e))
        return jsonify({'error': f'Error sending direct notification: {str(e)}'}), 500 

@fcm_routes.route('/fcm/test/email-notification', methods=['POST'])
def test_email_notification():
    """
    Test email notification (no authentication required)
    """
    try:
        print('🧪 Testing email notification...')
        
        # Get all FCM tokens
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute('SELECT token FROM fcm_tokens WHERE is_active = TRUE')
        tokens = [row[0] for row in cur.fetchall()]
        cur.close()
        return_db_conn(conn)
        
        if tokens:
            fcm_service_fallback.send_notification(
                tokens=tokens,
                title='📧 You have new email',
                body='New customer email received',
                data={
                    'type': 'new_email',
                    'email_id': '999',
                    'timestamp': datetime.now().isoformat()
                }
            )
            print(f"✅ Test email notification sent to {len(tokens)} tokens")
            return jsonify({
                'message': 'Test email notification sent successfully',
                'tokens_count': len(tokens)
            }), 200
        else:
            print("ℹ️ No FCM tokens found for test")
            return jsonify({
                'message': 'No FCM tokens found',
                'tokens_count': 0
            }), 200
            
    except Exception as e:
        print('🧪 Error sending test email notification:', str(e))
        return jsonify({'error': f'Error sending test email notification: {str(e)}'}), 500 

@fcm_routes.route('/fcm/check-email-status', methods=['GET'])
def check_email_status():
    """
    Check email processing status and trigger manual email check
    """
    try:
        print('📧 Checking email processing status...')
        
        # Try to import and run email processing
        try:
            from email_ingestor import process_inbox
            print('📧 Email ingestor imported successfully')
            
            # Run a manual email check
            print('📧 Running manual email check...')
            results = process_inbox()
            
            print(f'📧 Email check completed. Processed {len(results)} emails')
            
            return jsonify({
                'message': 'Email processing check completed',
                'emails_processed': len(results),
                'results': results
            }), 200
            
        except ImportError as e:
            print(f'📧 Error importing email ingestor: {e}')
            return jsonify({
                'error': 'Email ingestor not available',
                'details': str(e)
            }), 500
            
    except Exception as e:
        print('📧 Error checking email status:', str(e))
        return jsonify({'error': f'Error checking email status: {str(e)}'}), 500 

@fcm_routes.route('/debug-token', methods=['GET'])
@jwt_required()
def debug_fcm_token():
    """Debug endpoint to show current user's FCM tokens"""
    try:
        user_id = get_jwt_identity()
        
        # Get all FCM tokens for this user from the correct table
        conn = get_db_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT token, created_at, updated_at FROM fcm_tokens 
            WHERE user_id = %s
            ORDER BY updated_at DESC
        """, (user_id,))
        
        tokens = cursor.fetchall()
        cursor.close()
        return_db_conn(conn)
        
        if tokens:
            token_list = []
            for i, (token, created_at, updated_at) in enumerate(tokens):
                token_list.append({
                    'device': f'Device {i+1}',
                    'token': token,
                    'token_length': len(token),
                    'token_preview': token[:50] + '...' if len(token) > 50 else token,
                    'created_at': created_at.isoformat() if created_at else None,
                    'updated_at': updated_at.isoformat() if updated_at else None
                })
            
            return jsonify({
                'message': f'Found {len(tokens)} FCM token(s) for this user',
                'tokens': token_list,
                'total_tokens': len(tokens)
            })
        else:
            return jsonify({
                'message': 'No FCM tokens found for this user',
                'tokens': [],
                'total_tokens': 0
            })
            
    except Exception as e:
        return jsonify({'error': f'Error getting FCM tokens: {str(e)}'}), 500 