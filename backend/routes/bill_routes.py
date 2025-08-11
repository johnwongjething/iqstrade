from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.security import encrypt_sensitive_data, decrypt_sensitive_data, validate_password
from config import get_db_conn, return_db_conn
from utils.helpers import get_hk_date_range
import os
import cloudinary
import cloudinary.uploader
from cloudinary_utils import upload_filelike_to_cloudinary, upload_filepath_to_cloudinary
import json
import pytz
from datetime import datetime
from email_utils import send_unique_number_email, send_invoice_email, send_simple_email
from invoice_utils import generate_invoice_pdf
import tempfile
from ocr_processor import extract_fields_openai
from extract_fields import extract_fields as extract_fields_legacy
from ocr_processor_enhanced_v5 import extract_fields_openai_enhanced_v5

bill_routes = Blueprint('bill_routes', __name__)
# Migration: Removed UPLOAD_FOLDER, switching to Cloudinary for all file storage

def convert_decimals_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if hasattr(value, '__class__') and value.__class__.__name__ == 'Decimal':
                obj[key] = float(value)
            elif isinstance(value, (dict, list)):
                convert_decimals_to_float(value)
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            if hasattr(value, '__class__') and value.__class__.__name__ == 'Decimal':
                obj[i] = float(value)
            elif isinstance(value, (dict, list)):
                convert_decimals_to_float(value)
    return obj

# Bill and file-related endpoints
# /bills, /bill/<id>, /uploads/<filename>, /upload, /bill/<id>/upload_receipt, /bill/<id>/unique_number, /send_unique_number_email, /send_invoice_email, /bill/<id>/delete, /generate_payment_link/<id>, /bills/status/<status>, /bills/awaiting_bank_in

# --- AUTO-INVOICE GENERATION FUNCTION ---
def auto_generate_invoice_for_bill(bill):
            # Checking OCR completeness for BL id {bill['id']}
    try:
        ocr_fields = json.loads(bill.get('ocr_text') or '{}')
    except Exception as e:
        print(f"[ERROR] Could not parse ocr_text for BL id {bill['id']}: {e}")
        return False

    required = [
        'shipper', 'consignee', 'port_of_loading', 'port_of_discharge',
        'bl_number', 'container_numbers', 'flight_or_vessel'
    ]
    missing = [field for field in required if not ocr_fields.get(field)]
    if missing:
        # OCR incomplete for BL id {bill['id']}, missing: {missing}. Skipping automation.
        return False

            # OCR complete, proceeding with auto-invoice for BL id {bill['id']}
    conn = get_db_conn()
    cur = conn.cursor()

    # Use calculated fees from enhanced OCR, fallback to container-based calculation
    ctn_fee = bill.get('calculated_ctn_fee')
    service_fee = bill.get('calculated_service_fee')
    
    # Fallback to container-based calculation if calculated fees are not available
    if ctn_fee is None or service_fee is None:
        import re
        container_numbers = bill.get('container_numbers', '')
        container_list = [c for c in re.split(r'[,\s]+', container_numbers.strip()) if c]
        num_containers = len(container_list) if container_list else 1
        ctn_fee = 100 * num_containers
        service_fee = 100 * num_containers
        # Using fallback fees
    else:
        pass  # Using calculated fees

    # --- Unique number generation and DB update ---
    import random
    import string
    unique_number = bill.get('unique_number')
    if not unique_number:
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=6))
        unique_number = letters + numbers
        # Update DB
        cur.execute("""
            UPDATE bill_of_lading SET unique_number = %s WHERE id = %s
        """, (unique_number, bill['id']))
        conn.commit()

    # Generate payment link (after fees and unique_number are set)
    payment_link = bill.get('payment_link')
    if not payment_link:
        payment_link = f"https://pay.example.com/{bill['id']}?ctn={ctn_fee}&svc={service_fee}&uniquenum={unique_number}"

    # Generate invoice PDF
            # Generating invoice PDF for BL id {bill['id']}
    customer = {
        'name': bill.get('customer_name', ''),
        'email': bill.get('customer_email', ''),
        'phone': bill.get('customer_phone', '')
    }

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        invoice_local_path = tmp.name

    generate_invoice_pdf(customer, bill, service_fee, ctn_fee, payment_link, output_path=invoice_local_path)
            # Invoice generated at: {invoice_local_path}

            # Uploading to Cloudinary for BL id {bill['id']}
    cloud_url = upload_filepath_to_cloudinary(invoice_local_path, folder="invoices")
            # Invoice uploaded to Cloudinary: {cloud_url}

    # Update DB
    cur.execute("""
        UPDATE bill_of_lading
        SET ctn_fee=%s, service_fee=%s, payment_link=%s, invoice_filename=%s
        WHERE id=%s
    """, (ctn_fee, service_fee, payment_link, cloud_url, bill['id']))
    conn.commit()
            # DB updated with invoice_filename and payment_link for BL id {bill['id']}

    cur.close()
    conn.close()

    try:
        os.remove(invoice_local_path)
    except Exception:
        pass

    return True



@bill_routes.route('/bills', methods=['GET'])
@jwt_required()
def get_all_bills():
    user = json.loads(get_jwt_identity())
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))
    offset = (page - 1) * page_size
    bl_number = request.args.get('bl_number')
    status = request.args.get('status')
    date = request.args.get('date')
    conn = get_db_conn()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cur = conn.cursor()
    where_clauses = []
    params = []
    if bl_number:
        where_clauses.append('bl_number ILIKE %s')
        params.append(f'%{bl_number}%')
    if status:
        where_clauses.append('status = %s')
        params.append(status)
    if date:
        start_date, end_date = get_hk_date_range(date)
        where_clauses.append('created_at >= %s AND created_at < %s')
        params.extend([start_date, end_date])
    where_sql = ' AND '.join(where_clauses)
    if where_sql:
        where_sql = 'WHERE ' + where_sql
    count_query = f'SELECT COUNT(*) FROM bill_of_lading {where_sql}'
    cur.execute(count_query, tuple(params))
    total_count = cur.fetchone()[0]
    query = f'''
        SELECT id, customer_name, customer_email, customer_phone, pdf_filename, shipper, consignee, notify_party, port_of_loading, port_of_discharge, bl_number, container_numbers,
               flight_or_vessel, product_description, service_fee, ctn_fee, calculated_ctn_fee, calculated_service_fee, payment_link, receipt_filename, status, invoice_filename, unique_number, created_at, receipt_uploaded_at, customer_username, customer_invoice, customer_packing_list,
               shipment_type, container_type, container_count, container_count_20ft, container_count_40ft, container_count_40ft_hc, total_weight_kg, weight_unit, pricing_method, ocr_confidence_score, pricing_calculation_log, balance_applied
        FROM bill_of_lading
        {where_sql}
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    '''
    cur.execute(query, tuple(params) + (page_size, offset))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    bills = []
    for row in rows:
        bill_dict = dict(zip(columns, row))
        if bill_dict.get('customer_email') is not None:
            bill_dict['customer_email'] = decrypt_sensitive_data(bill_dict['customer_email'])
        if bill_dict.get('customer_phone') is not None:
            bill_dict['customer_phone'] = decrypt_sensitive_data(bill_dict['customer_phone'])
        # Convert Decimal objects to float
        convert_decimals_to_float(bill_dict)
        
        # Container and vessel info processed
        
        bills.append(bill_dict)
    cur.close()
    conn.close()
    return jsonify({
        'bills': bills,
        'total': total_count,
        'page': page,
        'page_size': page_size
    })

@bill_routes.route('/bill/<int:id>', methods=['GET'])
@jwt_required()
def get_bill(id):
    user = json.loads(get_jwt_identity())
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bill_of_lading WHERE id=%s", (id,))
    bill_row = cur.fetchone()
    if not bill_row:
        cur.close()
        conn.close()
        return jsonify({'error': 'Bill not found'}), 404
    columns = [desc[0] for desc in cur.description]
    bill = dict(zip(columns, bill_row))
    if bill.get('customer_email') is not None:
        bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
    if bill.get('customer_phone') is not None:
        bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])
    # Convert Decimal objects to float
    convert_decimals_to_float(bill)
    cur.close()
    conn.close()
      # --- AUTO-INVOICE GENERATION ---
    # Removed auto-invoice generation from GET /bill/<id>

    return jsonify(bill)

# @bill_routes.route('/uploads/<path:filename>', methods=['GET'])
# @jwt_required()
# def uploaded_file(filename):
#     from urllib.parse import unquote
#     safe_filename = unquote(filename)
#     full_path = os.path.join(UPLOAD_FOLDER, safe_filename)
#     print(f"Debug: Serving {safe_filename} from {full_path}, Exists: {os.path.exists(full_path)}")
#     try:
#         response = send_from_directory(UPLOAD_FOLDER, safe_filename)
#         if response.headers.get('X-Frame-Options'):
#             del response.headers['X-Frame-Options']
#         if safe_filename.lower().endswith('.pdf'):
#             response.headers['Content-Type'] = 'application/pdf'
#         return response
#     except FileNotFoundError:
#         print(f"Error: File not found at {full_path}")
#         return "File not found", 404
#     except Exception as e:
#         print(f"[ERROR] Exception serving file: {e}")
#         return f"Error serving file: {str(e)}", 500

@bill_routes.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    from extract_fields import extract_fields
    from email_utils import send_simple_email
    from config import EmailConfig
    # [DEBUG] Migration: No local upload dir, using Cloudinary
    user = json.loads(get_jwt_identity())
    username = user['username']
    # Upload triggered by username
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        bill_pdfs = request.files.getlist('bill_pdf')
        invoice_pdf = request.files.get('invoice_pdf')
        packing_pdf = request.files.get('packing_pdf')
        
        # Debug: Print what we received
        print(f"🔍 DEBUG - Form data received:")
        print(f"  name: '{name}'")
        print(f"  email: '{email}'")
        print(f"  phone: '{phone}'")
        print(f"  bill_pdfs count: {len(bill_pdfs)}")
        print(f"  invoice_pdf: {invoice_pdf is not None}")
        print(f"  packing_pdf: {packing_pdf is not None}")
        print(f"  All form keys: {list(request.form.keys())}")
        print(f"  All files keys: {list(request.files.keys())}")
        
        # Use username as fallback if name is empty
        if not name or not name.strip():
            name = username
        
        if not email:
            print(f"❌ Email validation failed - email is empty or None")
            return jsonify({'error': 'Email is required'}), 400
        if not phone:
            print(f"❌ Phone validation failed - phone is empty or None")
            return jsonify({'error': 'Phone is required'}), 400
        if not bill_pdfs and not invoice_pdf and not packing_pdf:
            return jsonify({'error': 'At least one PDF file is required'}), 400
        import tempfile
        # PDF compression logic removed, using original file for extract_fields

        def save_file_with_timestamp_and_cloudinary(file, label):
            if not file:
                return None, None, None
            ext = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                file.save(tmp.name)
                local_path = tmp.name
            # Upload to Cloudinary (always original)
            cloud_url = upload_filepath_to_cloudinary(local_path, folder=label)
            return cloud_url, local_path, file.filename
        uploaded_count = 0
        customer_invoice = None
        customer_packing_list = None
        if invoice_pdf:
            customer_invoice, invoice_local_path, invoice_orig_filename = save_file_with_timestamp_and_cloudinary(invoice_pdf, 'invoice')
            try:
                os.remove(invoice_local_path)
            except Exception:
                pass
        if packing_pdf:
            customer_packing_list, packing_local_path, packing_orig_filename = save_file_with_timestamp_and_cloudinary(packing_pdf, 'packing')
            try:
                os.remove(packing_local_path)
            except Exception:
                pass
        if bill_pdfs:
            for bill_pdf in bill_pdfs:
                pdf_url, local_path, orig_filename = save_file_with_timestamp_and_cloudinary(bill_pdf, 'bill')
                fields = {}
                ocr_status = "failed"
                if bill_pdf:
                    try:
                        if username == 'ray40':
                            # User ray40 uses OpenAI OCR
                            fields = extract_fields_openai_enhanced_v5(local_path)
                            ocr_status = "success" if fields else "failed"
                        else:
                            # Other users use Google Vision OCR
                            fields = extract_fields_legacy(local_path)
                            ocr_status = "success" if fields else "failed"
                    except Exception as e:
                        # Fallback to legacy extraction
                        try:
                            if username == 'ray40':
                                # Fallback for ray40: try OpenAI again
                                fields = extract_fields_openai_enhanced_v5(local_path)
                            else:
                                # Fallback for others: try legacy again
                                fields = extract_fields_legacy(local_path)
                            ocr_status = "success" if fields else "failed"
                        except Exception as e2:
                            fields = {}
                            ocr_status = "failed"
                
                # Ensure we always have basic fields even if OCR fails
                if not fields:
                    fields = {
                        'shipper': '',
                        'consignee': '',
                        'notify_party': '',
                        'port_of_loading': '',
                        'port_of_discharge': '',
                        'bl_number': '',
                        'container_numbers': '',
                        'flight_or_vessel': '',
                        'product_description': '',
                        'shipment_type': 'ocean',
                        'container_count': 1,
                        'container_count_20ft': 0,
                        'container_count_40ft': 0,
                        'container_count_40ft_hc': 0,
                        'total_weight_kg': None,
                        'weight_unit': 'kg',
                        'pricing_method': 'container',
                        'calculated_ctn_fee': None,
                        'calculated_service_fee': None,
                        'ocr_confidence_score': 0.0,
                        'pricing_calculation_log': {},
                        'ocr_status': ocr_status
                    }
                
                fields_json = json.dumps(fields)
                hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
                conn = get_db_conn()
                cur = conn.cursor()
                
                # Use enhanced fields for database insertion
                cur.execute("""
                    INSERT INTO bill_of_lading (
                        customer_name, customer_email, customer_phone, pdf_filename, ocr_text,
                        shipper, consignee, notify_party, port_of_loading, port_of_discharge, bl_number, container_numbers,
                        flight_or_vessel, product_description, status,
                        customer_username, created_at, customer_invoice, customer_packing_list,
                        shipment_type, container_type, container_count, container_count_20ft, container_count_40ft, container_count_40ft_hc,
                        total_weight_kg, weight_unit, pricing_method, calculated_ctn_fee, calculated_service_fee, 
                        ocr_confidence_score, pricing_calculation_log
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    name, str(email), str(phone), pdf_url, fields_json,
                    str(fields.get('shipper', '')),
                    str(fields.get('consignee', '')),
                    str(fields.get('notify_party', '')),
                    str(fields.get('port_of_loading', '')),
                    str(fields.get('port_of_discharge', '')),
                    str(fields.get('bl_number', '')),
                    str(fields.get('container_numbers', '')),
                    str(fields.get('flight_or_vessel', '')),
                    str(fields.get('product_description', '')),
                    "Pending",
                    username,
                    hk_now,
                    customer_invoice,
                    customer_packing_list,
                    fields.get('shipment_type', 'ocean'),
                    fields.get('container_type'),
                    fields.get('container_count', 1),
                    fields.get('container_count_20ft', 0),
                    fields.get('container_count_40ft', 0),
                    fields.get('container_count_40ft_hc', 0),
                    fields.get('total_weight_kg'),
                    fields.get('weight_unit', 'kg'),
                    fields.get('pricing_method', 'container'),
                    fields.get('calculated_ctn_fee'),
                    fields.get('calculated_service_fee'),
                    fields.get('ocr_confidence_score'),
                    json.dumps(fields.get('pricing_calculation_log', {}))
                ))
                conn.commit()
                
                # Fetch newly inserted BOL row
                cur.execute("SELECT * FROM bill_of_lading WHERE id = (SELECT MAX(id) FROM bill_of_lading)")
                bill_row = cur.fetchone()
                columns = [desc[0] for desc in cur.description]
                bill = dict(zip(columns, bill_row)) if bill_row else None
                
                # Convert Decimal objects to float for JSON serialization
                if bill:
                    convert_decimals_to_float(bill)
                
                if bill:
                    if username == 'ray40':
                        auto_generate_invoice_for_bill(bill)
                cur.close()
                conn.close()
                uploaded_count += 1
                # Clean up temp files
                try:
                    os.remove(local_path)
                except Exception:
                    pass
        else:
            hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO bill_of_lading (
                    customer_name, customer_email, customer_phone, pdf_filename, ocr_text,
                    shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers, status,
                    customer_username, created_at, customer_invoice, customer_packing_list
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                name, str(email), str(phone), None, None,
                '', '', '', '', '', '',
                "Pending",
                username,
                hk_now,
                customer_invoice,
                customer_packing_list
            ))
            conn.commit()
            cur.close()
            conn.close()
            uploaded_count += 1
        # Send confirmation email if SMTP is configured
        try:
            if EmailConfig.SMTP_SERVER and EmailConfig.SMTP_USERNAME and EmailConfig.SMTP_PASSWORD:
                subject = "We have received your Bill of Lading"
                body = f"Dear {name},\n\nWe have received your documents. Our team will be in touch with you within 24 hours.\n\nThank you!"
                send_simple_email(email, subject, body)
        except Exception as e:
            print(f"Failed to send confirmation email: {str(e)}")
        
        # Send FCM push notification for new file upload
        try:
            from fcm_service_fallback import fcm_service_fallback
            # Get all FCM tokens for notifications
            conn = get_db_conn()
            cur = conn.cursor()
            
            # Try different possible column names for the token - ONE PER USER to prevent duplicates
            try:
                cur.execute("""
                    SELECT DISTINCT ON (user_id) token 
                    FROM fcm_tokens 
                    WHERE is_active = TRUE 
                    ORDER BY user_id, updated_at DESC
                """)
            except:
                try:
                    cur.execute("""
                        SELECT DISTINCT ON (user_id) fcm_token 
                        FROM fcm_tokens 
                        WHERE is_active = TRUE 
                        ORDER BY user_id, updated_at DESC
                    """)
                except:
                    try:
                        cur.execute('SELECT * FROM fcm_tokens LIMIT 1')
                        columns = [desc[0] for desc in cur.description]
                        token_column = next((col for col in columns if 'token' in col.lower()), 'token')
                        cur.execute(f"""
                            SELECT DISTINCT ON (user_id) {token_column} 
                            FROM fcm_tokens 
                            WHERE is_active = TRUE 
                            ORDER BY user_id, updated_at DESC
                        """)
                    except Exception as e:
                        print(f"Could not query fcm_tokens table: {e}")
                        tokens = []
                        return
            
            tokens = [row[0] for row in cur.fetchall()]
            cur.close()
            return_db_conn(conn)
            
            if tokens:
                result = fcm_service_fallback.send_notification(
                    tokens=tokens,
                    title='📁 New File Upload',
                    body=f'{uploaded_count} new bill(s) uploaded by {name}',
                    data={
                        'type': 'new_upload',
                        'uploader': name,
                        'count': str(uploaded_count),  # Convert to string
                        'timestamp': datetime.now().isoformat()
                    }
                )
                
                if result['success']:
                    api_used = result.get('api_used', 'unknown')
                    print(f"✅ FCM notification sent for new upload: {uploaded_count} files by {name} (API: {api_used})")
                else:
                    print(f"❌ FCM notification failed: {result.get('error', 'Unknown error')}")
            else:
                print("ℹ️ No FCM tokens found for notifications")
        except Exception as e:
            print(f"Failed to send FCM notification: {str(e)}")
        
        return jsonify({'message': f'Upload successful! {uploaded_count} bill(s) uploaded.'})
    except Exception as e:
        return jsonify({'error': f'Error processing upload: {str(e)}'}), 400

@bill_routes.route('/bill/<int:id>/upload_receipt', methods=['POST'])
@jwt_required()
def upload_receipt(id):
    user = json.loads(get_jwt_identity())
    username = user['username']
    try:
        receipt = request.files.get('receipt')
        if not receipt:
            return jsonify({'error': 'Receipt PDF file is required'}), 400
        cloud_url = upload_filelike_to_cloudinary(receipt, folder="receipts")
        hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE bill_of_lading
            SET receipt_filename = %s, status = %s, receipt_uploaded_at = %s
            WHERE id = %s
        """, (cloud_url, 'Awaiting Bank In', hk_now, id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Receipt uploaded'})
    except Exception as e:
        return jsonify({'error': f'Error processing receipt upload: {str(e)}'}), 400

@bill_routes.route('/bill/<int:id>/unique_number', methods=['POST'])
@jwt_required()
def set_unique_number(id):
    user = json.loads(get_jwt_identity())
    username = user['username']
    try:
        unique_number = request.json.get('unique_number')
        if not unique_number:
            return jsonify({'error': 'Unique number is required'}), 400
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE bill_of_lading
            SET unique_number = %s
            WHERE id = %s
        """, (unique_number, id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Unique number set successfully'})
    except Exception as e:
        return jsonify({'error': f'Error setting unique number: {str(e)}'}), 400

@bill_routes.route('/send_unique_number_email', methods=['POST'])
@jwt_required()
def send_unique_number_email():
    user = json.loads(get_jwt_identity())
    username = user['username']
    try:
        data = request.get_json()
        bill_id = data.get('id') or data.get('bill_id')
        to_email = data.get('to_email')
        subject = data.get('subject', 'Your Unique Number')
        body = data.get('body', '')
        if not bill_id or not to_email or not subject or not body:
            return jsonify({'error': 'Missing required fields'}), 400
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM bill_of_lading WHERE id=%s", (bill_id,))
        bill_row = cur.fetchone()
        if not bill_row:
            cur.close()
            conn.close()
            return jsonify({'error': 'Bill not found'}), 404
        columns = [desc[0] for desc in cur.description]
        bill = dict(zip(columns, bill_row))
        if bill.get('customer_email') is not None:
            bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
        if bill.get('customer_phone') is not None:
            bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])
        cur.close()
        conn.close()
        from email_utils import send_unique_number_email as send_unique_number_email_util
        send_unique_number_email_util(to_email, subject, body)
        return jsonify({'message': 'Unique number email sent successfully'})
    except Exception as e:
        return jsonify({'error': f'Error sending unique number email: {str(e)}'}), 400

@bill_routes.route('/send_invoice_email', methods=['POST'])
@jwt_required()
def send_invoice_email():
    user = json.loads(get_jwt_identity())
    username = user['username']
    try:
        data = request.get_json()
        bill_id = data.get('id') or data.get('bill_id')
        if not bill_id:
            return jsonify({'error': 'ID is required'}), 400
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM bill_of_lading WHERE id=%s", (bill_id,))
        bill_row = cur.fetchone()
        if not bill_row:
            cur.close()
            conn.close()
            return jsonify({'error': 'Bill not found'}), 404
        columns = [desc[0] for desc in cur.description]
        bill = dict(zip(columns, bill_row))
        if bill.get('customer_email') is not None:
            bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
        if bill.get('customer_phone') is not None:
            bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])
        # Use custom email fields if provided, else fallback to defaults
        to_email = data.get('to_email', bill['customer_email'])
        subject = data.get('subject', 'Your Invoice')
        body = data.get('body', 'Please find your invoice attached.')
        pdf_url = data.get('pdf_url')
        # Use Cloudinary URL directly
        from email_utils import send_invoice_email as send_invoice_email_util
        success = send_invoice_email_util(to_email, subject, body, pdf_url)
        if success:
            cur.execute("UPDATE bill_of_lading SET status=%s WHERE id=%s", ("Invoice Sent", bill_id))
            conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Invoice email sent successfully'})
    except Exception as e:
        return jsonify({'error': f'Error sending invoice email: {str(e)}'}), 400

@bill_routes.route('/bill/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_bill(id):
    user = json.loads(get_jwt_identity())
    username = user['username']
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM bill_of_lading WHERE id=%s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Bill deleted successfully'})
    except Exception as e:
        return jsonify({'error': f'Error deleting bill: {str(e)}'}), 400


@bill_routes.route('/bills/status/<string:status>', methods=['GET'])
@jwt_required()
def get_bills_by_status(status):
    user = json.loads(get_jwt_identity())
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))
    offset = (page - 1) * page_size
    conn = get_db_conn()
    cur = conn.cursor()
    query = f'''
        SELECT id, customer_name, customer_email, customer_phone, pdf_filename, shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers,
               flight_or_vessel, product_description, service_fee, ctn_fee, payment_link, receipt_filename, status, invoice_filename, unique_number, created_at, receipt_uploaded_at, customer_username, customer_invoice, customer_packing_list
        FROM bill_of_lading
        WHERE status = %s
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    '''
    cur.execute(query, (status, page_size, offset))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    bills = []
    for row in rows:
        bill_dict = dict(zip(columns, row))
        if bill_dict.get('customer_email') is not None:
            bill_dict['customer_email'] = decrypt_sensitive_data(bill_dict['customer_email'])
        if bill_dict.get('customer_phone') is not None:
            bill_dict['customer_phone'] = decrypt_sensitive_data(bill_dict['customer_phone'])
        bills.append(bill_dict)
    cur.close()
    conn.close()
    return jsonify({
        'bills': bills,
        'total': len(bills),
        'page': page,
        'page_size': page_size
    })

@bill_routes.route('/bills/awaiting_bank_in', methods=['GET'])
@jwt_required()
def get_awaiting_bank_in_bills():
    try:
        bl_number = request.args.get('bl_number', '').strip()
        conn = get_db_conn()
        cur = conn.cursor()

        where_clauses = []
        params = []

        # Include reserve_status = 'Unsettled' bills as well
        if bl_number:
            where_clauses.append(
                "((status = 'Awaiting Bank In' AND bl_number ILIKE %s) OR "
                "(payment_method = 'Allinpay' AND payment_status = 'Paid 85%' AND bl_number ILIKE %s) OR "
                "(LOWER(TRIM(reserve_status)) = 'unsettled' AND bl_number ILIKE %s))"
            )
            params.extend([f"%{bl_number}%", f"%{bl_number}%", f"%{bl_number}%"])
        else:
            where_clauses.append(
                "((status = 'Awaiting Bank In') OR "
                "(payment_method = 'Allinpay' AND payment_status = 'Paid 85%') OR "
                "(LOWER(TRIM(reserve_status)) = 'unsettled'))"
            )

        where_sql = " AND ".join(where_clauses)
        query = (
            "SELECT * FROM bill_of_lading "
            "WHERE " + where_sql + " "
            "ORDER BY id DESC"
        )

        if params:
            cur.execute(query, tuple(params))
        else:
            cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        bills = []
        for row in rows:
            bill_dict = dict(zip(columns, row))
            # Decrypt email and phone if needed
            if bill_dict.get('customer_email') is not None:
                bill_dict['customer_email'] = decrypt_sensitive_data(bill_dict['customer_email'])
            if bill_dict.get('customer_phone') is not None:
                bill_dict['customer_phone'] = decrypt_sensitive_data(bill_dict['customer_phone'])
            bills.append(bill_dict)

        return jsonify({'bills': bills, 'total': len(bills)})
    except Exception as e:
        print("❌ ERROR in awaiting_bank_in:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass

@bill_routes.route('/bill/<int:id>', methods=['PUT'])
@jwt_required()
def update_bill(id):
    user = json.loads(get_jwt_identity())
    try:
        data = request.get_json()
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM bill_of_lading WHERE id=%s", (id,))
        bill_row = cur.fetchone()
        if not bill_row:
            return jsonify({'error': 'Bill not found'}), 404
        columns = [desc[0] for desc in cur.description]
        bill = dict(zip(columns, bill_row))
        updatable_fields = [
            'customer_name', 'customer_email', 'customer_phone', 'bl_number',
            'shipper', 'consignee', 'port_of_loading', 'port_of_discharge',
            'container_numbers', 'service_fee', 'ctn_fee', 'payment_link', 'unique_number',
            'flight_or_vessel', 'product_description',
            'payment_method', 'payment_status', 'reserve_status', 'balance_applied'
        ]
        update_fields = []
        update_values = []
        for field in updatable_fields:
            if field in data and data[field] is not None:
                if field == 'customer_email':
                    update_fields.append(f"{field}=%s")
                    update_values.append(encrypt_sensitive_data(data[field]))
                elif field == 'customer_phone':
                    update_fields.append(f"{field}=%s")
                    update_values.append(encrypt_sensitive_data(data[field]))
                else:
                    update_fields.append(f"{field}=%s")
                    update_values.append(data[field])
        if update_fields:
            update_values.append(id)
            update_query = f"""
                UPDATE bill_of_lading
                SET {', '.join(update_fields)}
                WHERE id=%s
            """
            cur.execute(update_query, tuple(update_values))
            conn.commit()
        cur.execute("SELECT * FROM bill_of_lading WHERE id=%s", (id,))
        bill_row = cur.fetchone()
        columns = [desc[0] for desc in cur.description]
        bill = dict(zip(columns, bill_row))
        if bill.get('customer_email') is not None:
            bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
        if bill.get('customer_phone') is not None:
            bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])
        import tempfile
        try:
            customer = {
                'name': bill['customer_name'],
                'email': bill['customer_email'],
                'phone': bill['customer_phone']
            }
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                invoice_local_path = tmp.name
            # Pass the temp file path to generate_invoice_pdf so it writes to the correct location
            generate_invoice_pdf(customer, bill, bill.get('service_fee'), bill.get('ctn_fee'), bill.get('payment_link'), bill.get('balance_applied', 0), output_path=invoice_local_path)
            cloud_url = upload_filepath_to_cloudinary(invoice_local_path, folder="invoices")
            bill['invoice_filename'] = cloud_url
            # Save Cloudinary URL to DB
            cur.execute("UPDATE bill_of_lading SET invoice_filename=%s WHERE id=%s", (cloud_url, id))
            conn.commit()
            # Delete local file
            if os.path.exists(invoice_local_path):
                os.remove(invoice_local_path)
        except Exception as e:
            import traceback
            traceback.print_exc()
        cur.close()
        conn.close()
        return jsonify(bill)
    except Exception as e:
        return jsonify({'error': f'Error updating bill: {str(e)}'}), 400

@bill_routes.route('/bill/<int:id>/settle_reserve', methods=['POST'])
@jwt_required()
def settle_reserve(id):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM bill_of_lading WHERE id = %s", (id,))
        if not cur.fetchone():
            return jsonify({"error": "Bill not found"}), 404
        cur.execute("""
            UPDATE bill_of_lading
            SET reserve_status = 'Reserve Settled'
            WHERE id = %s
        """, (id,))
        conn.commit()
        return jsonify({"message": "Reserve marked as settled"}), 200
    except Exception as e:
        return jsonify({"error": "Failed to settle reserve"}), 500
    finally:
        cur.close()
        conn.close()

@bill_routes.route('/bill/<int:id>/complete', methods=['POST'])
@jwt_required()
def complete_bill(id):
    conn = get_db_conn()
    cur = conn.cursor()
    hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
    cur.execute("SELECT payment_method FROM bill_of_lading WHERE id=%s", (id,))
    row = cur.fetchone()
    if row and row[0] and row[0].lower() == 'allinpay':
        cur.execute("""
            UPDATE bill_of_lading
            SET status=%s, payment_status=%s, completed_at=%s
            WHERE id=%s
        """, ('Paid and CTN Valid', 'Paid 100%', hk_now, id))
    else:
        cur.execute("""
            UPDATE bill_of_lading
            SET status=%s, completed_at=%s
            WHERE id=%s
        """, ('Paid and CTN Valid', hk_now, id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Bill marked as completed'})

@bill_routes.route('/search_bills', methods=['POST'])
@jwt_required()
def search_bills():
    data = request.get_json()
    customer_name = data.get('customer_name', '')
    customer_id = data.get('customer_id', '')
    created_at = data.get('created_at', '')
    bl_number = data.get('bl_number', '')
    unique_number = data.get('unique_number', '')
    username = data.get('username', '')
    conn = get_db_conn()
    cur = conn.cursor()
    query = '''
        SELECT id, customer_name, customer_email, customer_phone, pdf_filename, shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers, service_fee, ctn_fee, payment_link, receipt_filename, status, invoice_filename, unique_number, created_at, receipt_uploaded_at, customer_username, customer_invoice, customer_packing_list
        FROM bill_of_lading
        WHERE 1=1
    '''
    params = []
    if customer_name:
        query += ' AND customer_name ILIKE %s'
        params.append(f'%{customer_name}%')
    if customer_id:
        try:
            int(customer_id)
            query += ' AND id = %s'
            params.append(customer_id)
        except ValueError:
            query += ' AND customer_name ILIKE %s'
            params.append(f'%{customer_id}%')
    if created_at:
        start_date, end_date = get_hk_date_range(created_at)
        query += ' AND created_at >= %s AND created_at < %s'
        params.extend([start_date, end_date])
    if bl_number:
        query += ' AND bl_number ILIKE %s'
        params.append(f'%{bl_number}%')
    if unique_number:
        query += ' AND unique_number = %s'
        params.append(unique_number)
    if username:
        query += ' AND customer_username = %s'
        params.append(username)
    query += ' ORDER BY id DESC'
    cur.execute(query, params)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    bills = []
    for row in rows:
        bill_dict = dict(zip(columns, row))
        if bill_dict.get('customer_email') is not None:
            bill_dict['customer_email'] = decrypt_sensitive_data(bill_dict['customer_email'])
        if bill_dict.get('customer_phone') is not None:
            bill_dict['customer_phone'] = decrypt_sensitive_data(bill_dict['customer_phone'])
        bills.append(bill_dict)
    cur.close()
    conn.close()
    return jsonify(bills)

@bill_routes.route('/account_bills', methods=['GET'])
@jwt_required()
def account_bills():
    from dateutil import parser
    completed_at = request.args.get('completed_at')
    bl_number = request.args.get('bl_number')

    conn = get_db_conn()
    cur = conn.cursor()

    # Build base query
    select_clause = '''
        SELECT id, customer_name, customer_email, customer_phone, pdf_filename,
               shipper, consignee, port_of_loading, port_of_discharge, bl_number,
               container_numbers, service_fee, ctn_fee, payment_link, receipt_filename,
               status, invoice_filename, unique_number, created_at, receipt_uploaded_at,
               completed_at, allinpay_85_received_at,
               customer_username, customer_invoice, customer_packing_list,
               payment_method, payment_status, reserve_status
        FROM bill_of_lading
        WHERE status = 'Paid and CTN Valid'
    '''

    where_clauses = []
    params = []

    if completed_at:
        start_date, end_date = get_hk_date_range(completed_at)
        where_clauses.append(
            "((payment_method = 'Allinpay' AND allinpay_85_received_at >= %s AND allinpay_85_received_at < %s) "
            "OR (payment_method = 'Allinpay' AND completed_at >= %s AND completed_at < %s) "
            "OR (payment_method != 'Allinpay' AND completed_at >= %s AND completed_at < %s))"
        )
        params.extend([start_date, end_date, start_date, end_date, start_date, end_date])
    if bl_number:
        where_clauses.append("bl_number ILIKE %s")
        params.append(f'%{bl_number}%')

    if where_clauses:
        select_clause += " AND " + " AND ".join(where_clauses)

    select_clause += " ORDER BY id DESC"

    cur.execute(select_clause, tuple(params))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    bills = []
    total_bank_ctn = 0
    total_bank_service = 0
    total_allinpay_85_ctn = 0
    total_allinpay_85_service = 0
    total_reserve_ctn = 0
    total_reserve_service = 0

    for row in rows:
        bill = dict(zip(columns, row))

        # Decrypt sensitive fields
        if bill.get('customer_email'):
            bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
        if bill.get('customer_phone'):
            bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])

        try:
            ctn_fee = float(bill.get('ctn_fee') or 0)
            service_fee = float(bill.get('service_fee') or 0)
        except (TypeError, ValueError):
            ctn_fee = 0
            service_fee = 0

        # Default: show original values
        bill['display_ctn_fee'] = ctn_fee
        bill['display_service_fee'] = service_fee

        # 85%/15% logic for Allinpay
        if bill.get('payment_method') == 'Allinpay':
            allinpay_85_dt = bill.get('allinpay_85_received_at')
            is_85 = False
            if allinpay_85_dt:
                if isinstance(allinpay_85_dt, str):
                    try:
                        allinpay_85_dt = parser.isoparse(allinpay_85_dt)
                    except Exception:
                        allinpay_85_dt = None
                if allinpay_85_dt and allinpay_85_dt.tzinfo is None:
                    allinpay_85_dt = allinpay_85_dt.replace(tzinfo=pytz.UTC)
                if completed_at and allinpay_85_dt and start_date <= allinpay_85_dt < end_date:
                    bill['display_ctn_fee'] = round(ctn_fee * 0.85, 2)
                    bill['display_service_fee'] = round(service_fee * 0.85, 2)
                    total_allinpay_85_ctn += bill['display_ctn_fee']
                    total_allinpay_85_service += bill['display_service_fee']
                    is_85 = True
            reserve_status = (bill.get('reserve_status') or '').lower()
            completed_dt = bill.get('completed_at')
            if completed_dt:
                if isinstance(completed_dt, str):
                    try:
                        completed_dt = parser.isoparse(completed_dt)
                    except Exception:
                        completed_dt = None
                if completed_dt and completed_dt.tzinfo is None:
                    completed_dt = completed_dt.replace(tzinfo=pytz.UTC)
            if reserve_status in ['settled', 'reserve settled'] and completed_at and completed_dt and start_date <= completed_dt < end_date and not is_85:
                bill['display_ctn_fee'] = round(ctn_fee * 0.15, 2)
                bill['display_service_fee'] = round(service_fee * 0.15, 2)
                total_reserve_ctn += bill['display_ctn_fee']
                total_reserve_service += bill['display_service_fee']
        else:
            # Bank Transfer: always show full amount, but only count in summary if in date range
            completed_dt = bill.get('completed_at')
            if completed_dt:
                if isinstance(completed_dt, str):
                    try:
                        completed_dt = parser.isoparse(completed_dt)
                    except Exception:
                        completed_dt = None
                if completed_dt and completed_dt.tzinfo is None:
                    completed_dt = completed_dt.replace(tzinfo=pytz.UTC)
            if completed_at and completed_dt and start_date <= completed_dt < end_date:
                total_bank_ctn += ctn_fee
                total_bank_service += service_fee

        bills.append(bill)

    summary = {
        'totalEntries': len(bills),
        'totalCtnFee': round(total_bank_ctn + total_allinpay_85_ctn + total_reserve_ctn, 2),
        'totalServiceFee': round(total_bank_service + total_allinpay_85_service + total_reserve_service, 2),
        'bankTotal': round(total_bank_ctn + total_bank_service, 2),
        'allinpay85Total': round(total_allinpay_85_ctn + total_allinpay_85_service, 2),
        'reserveTotal': round(total_reserve_ctn + total_reserve_service, 2)
    }

    cur.close()
    conn.close()

    return jsonify({'bills': bills, 'summary': summary})


@bill_routes.route('/extract_fields', methods=['POST'])
@jwt_required()
def extract_fields_endpoint():
    """
    Expects a PDF file upload as 'pdf' in form-data.
    Returns extracted fields as JSON.
    Uses OpenAI for user 'ray40', Google Vision for others.
    """
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF file uploaded'}), 400
    pdf_file = request.files['pdf']
    user = json.loads(get_jwt_identity())
    username = user.get('username')
    # Save PDF to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf_path = tmp.name
        pdf_file.save(pdf_path)
    try:
        if username == 'ray40':
            # User ray40 uses OpenAI OCR
            fields = extract_fields_openai_enhanced_v5(pdf_path)
        else:
            # Other users use Google Vision OCR
            fields = extract_fields_legacy(pdf_path)
        return jsonify({'fields': fields})
    finally:
        try:
            os.remove(pdf_path)
        except Exception:
            pass


@bill_routes.route('/account_bills_monthly', methods=['GET'])
@jwt_required()
def account_bills_monthly():
    completed_month = request.args.get('completed_month')
    bl_number = request.args.get('bl_number')
    conn = get_db_conn()
    cur = conn.cursor()
    select_clause = '''
        SELECT id, customer_name, customer_email, customer_phone, pdf_filename,
               shipper, consignee, port_of_loading, port_of_discharge, bl_number,
               container_numbers, service_fee, ctn_fee, payment_link, receipt_filename,
               status, invoice_filename, unique_number, created_at, receipt_uploaded_at,
               completed_at, allinpay_85_received_at,
               customer_username, customer_invoice, customer_packing_list,
               payment_method, payment_status, reserve_status
        FROM bill_of_lading
        WHERE status = 'Paid and CTN Valid'
    '''
    where_clauses = []
    params = []
    if completed_month:
        # Parse YYYY-MM and get first and last day of month
        try:
            start_date = datetime.strptime(completed_month, '%Y-%m')
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            start_date = hk_tz.localize(start_date)
            # Get first day of next month, then subtract 1 second for end of month
            if start_date.month == 12:
                next_month = start_date.replace(year=start_date.year+1, month=1, day=1)
            else:
                next_month = start_date.replace(month=start_date.month+1, day=1)
            end_date = next_month
        except Exception as e:
            return jsonify({'error': 'Invalid completed_month format, should be YYYY-MM'}), 400
        where_clauses.append(
            "((payment_method = 'Allinpay' AND allinpay_85_received_at >= %s AND allinpay_85_received_at < %s) "
            "OR (payment_method = 'Allinpay' AND completed_at >= %s AND completed_at < %s) "
            "OR (payment_method != 'Allinpay' AND completed_at >= %s AND completed_at < %s))"
        )
        params.extend([start_date, end_date, start_date, end_date, start_date, end_date])
    if bl_number:
        where_clauses.append("bl_number ILIKE %s")
        params.append(f'%{bl_number}%')
    if where_clauses:
        select_clause += " AND " + " AND ".join(where_clauses)
    select_clause += " ORDER BY id DESC"
    cur.execute(select_clause, tuple(params))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    bills = []
    total_bank_ctn = 0
    total_bank_service = 0
    total_allinpay_85_ctn = 0
    total_allinpay_85_service = 0
    total_reserve_ctn = 0
    total_reserve_service = 0
    from dateutil import parser
    for row in rows:
        bill = dict(zip(columns, row))
        # Decrypt sensitive fields
        if bill.get('customer_email'):
            bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
        if bill.get('customer_phone'):
            bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])
        try:
            ctn_fee = float(bill.get('ctn_fee') or 0)
            service_fee = float(bill.get('service_fee') or 0)
        except (TypeError, ValueError):
            ctn_fee = 0
            service_fee = 0
        if bill.get('payment_method') == 'Allinpay':
            # 85% entry
            allinpay_85_dt = bill.get('allinpay_85_received_at')
            if allinpay_85_dt:
                if isinstance(allinpay_85_dt, str):
                    try:
                        allinpay_85_dt = parser.isoparse(allinpay_85_dt)
                    except Exception:
                        allinpay_85_dt = None
                if allinpay_85_dt and allinpay_85_dt.tzinfo is None:
                    allinpay_85_dt = allinpay_85_dt.replace(tzinfo=pytz.UTC)
                if completed_month and allinpay_85_dt and start_date <= allinpay_85_dt < end_date:
                    bill_85 = bill.copy()
                    bill_85['display_ctn_fee'] = round(ctn_fee * 0.85, 2)
                    bill_85['display_service_fee'] = round(service_fee * 0.85, 2)
                    bill_85['split_type'] = 'Allinpay 85%'
                    # Set the date field to allinpay_85_received_at for 85% split
                    bill_85['completed_at'] = bill.get('allinpay_85_received_at')
                    bills.append(bill_85)
                    total_allinpay_85_ctn += bill_85['display_ctn_fee']
                    total_allinpay_85_service += bill_85['display_service_fee']
            # 15% reserve entry
            reserve_status = (bill.get('reserve_status') or '').lower()
            completed_dt = bill.get('completed_at')
            if completed_dt:
                if isinstance(completed_dt, str):
                    try:
                        completed_dt = parser.isoparse(completed_dt)
                    except Exception:
                        completed_dt = None
                if completed_dt and completed_dt.tzinfo is None:
                    completed_dt = completed_dt.replace(tzinfo=pytz.UTC)
            if reserve_status in ['settled', 'reserve settled'] and completed_month and completed_dt and start_date <= completed_dt < end_date:
                bill_15 = bill.copy()
                bill_15['display_ctn_fee'] = round(ctn_fee * 0.15, 2)
                bill_15['display_service_fee'] = round(service_fee * 0.15, 2)
                bill_15['split_type'] = 'Allinpay Reserve'
                bills.append(bill_15)
                total_reserve_ctn += bill_15['display_ctn_fee']
                total_reserve_service += bill_15['display_service_fee']
        else:
            # Bank Transfer or other: single entry
            completed_dt = bill.get('completed_at')
            if completed_dt:
                if isinstance(completed_dt, str):
                    try:
                        completed_dt = parser.isoparse(completed_dt)
                    except Exception:
                        completed_dt = None
                if completed_dt and completed_dt.tzinfo is None:
                    completed_dt = completed_dt.replace(tzinfo=pytz.UTC)
            if completed_month and completed_dt and start_date <= completed_dt < end_date:
                bill_bank = bill.copy()
                bill_bank['display_ctn_fee'] = ctn_fee
                bill_bank['display_service_fee'] = service_fee
                bill_bank['split_type'] = 'Bank Transfer'
                bills.append(bill_bank)
                total_bank_ctn += ctn_fee
                total_bank_service += service_fee
    # Convert all 'completed_at' values to Asia/Hong_Kong timezone for display and sorting
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    def to_hk_time(val):
        if val is None:
            return None
        if isinstance(val, str):
            try:
                val = parser.isoparse(val)
            except Exception:
                return None
        if val.tzinfo is None:
            val = val.replace(tzinfo=pytz.UTC)
        return val.astimezone(hk_tz)


    # Also convert allinpay_85_received_at to HK time for all bills (for frontend display if needed)
    for bill in bills:
        # completed_at
        completed_at = bill.get('completed_at')
        hk_completed = to_hk_time(completed_at)
        if hk_completed:
            bill['completed_at'] = hk_completed.isoformat()
        else:
            bill['completed_at'] = None
        # allinpay_85_received_at
        allinpay_85 = bill.get('allinpay_85_received_at')
        hk_85 = to_hk_time(allinpay_85)
        if hk_85:
            bill['allinpay_85_received_at'] = hk_85.isoformat()
        else:
            bill['allinpay_85_received_at'] = None

    # Sort bills by HK time (descending), treating None as oldest
    def get_completed_at_hk(bill):
        val = bill.get('completed_at')
        if val is None:
            return datetime.min.replace(tzinfo=hk_tz)
        try:
            return parser.isoparse(val)
        except Exception:
            return datetime.min.replace(tzinfo=hk_tz)
    bills.sort(key=get_completed_at_hk, reverse=True)
    summary = {
        'totalEntries': len(bills),
        'totalCtnFee': round(total_bank_ctn + total_allinpay_85_ctn + total_reserve_ctn, 2),
        'totalServiceFee': round(total_bank_service + total_allinpay_85_service + total_reserve_service, 2),
        'bankTotal': round(total_bank_ctn + total_bank_service, 2),
        'allinpay85Total': round(total_allinpay_85_ctn + total_allinpay_85_service, 2),
        'reserveTotal': round(total_reserve_ctn + total_reserve_service, 2)
    }
    cur.close()
    conn.close()
    return jsonify({'bills': bills, 'summary': summary})

@bill_routes.route('/override_pricing', methods=['POST'])
@jwt_required()
def override_pricing_endpoint():
    """Manual override of pricing when OCR makes errors"""
    user = json.loads(get_jwt_identity())
    username = user['username']
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['bill_id', 'ctn_fee', 'service_fee', 'override_reason']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        conn = get_db_conn()
        cur = conn.cursor()
        
        # Get current bill data
        cur.execute("""
            SELECT ctn_fee, service_fee, calculated_ctn_fee, calculated_service_fee
            FROM bill_of_lading WHERE id = %s
        """, (data['bill_id'],))
        bill = cur.fetchone()
        
        if not bill:
            return jsonify({'error': 'Bill not found'}), 404
        
        original_ctn_fee, original_service_fee, calculated_ctn_fee, calculated_service_fee = bill
        
        # Update bill with override
        hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
        cur.execute("""
            UPDATE bill_of_lading
            SET ctn_fee = %s, service_fee = %s, manual_override = TRUE,
                override_reason = %s, override_by = %s, override_at = %s,
                last_pricing_update = %s
            WHERE id = %s
        """, (
            data['ctn_fee'], data['service_fee'], data['override_reason'],
            username, hk_now, hk_now, data['bill_id']
        ))
        
        # Log the override for audit
        cur.execute("""
            INSERT INTO pricing_overrides (
                bill_of_lading_id, original_ctn_fee, original_service_fee,
                new_ctn_fee, new_service_fee, reason, overridden_by, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['bill_id'], original_ctn_fee, original_service_fee,
            data['ctn_fee'], data['service_fee'], data['override_reason'],
            username, data.get('notes', '')
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'message': 'Pricing override saved successfully',
            'original_ctn_fee': original_ctn_fee,
            'original_service_fee': original_service_fee,
            'new_ctn_fee': data['ctn_fee'],
            'new_service_fee': data['service_fee']
        })
        
    except Exception as e:
        return jsonify({'error': f'Error saving override: {str(e)}'}), 400

@bill_routes.route('/recalculate_fees', methods=['POST'])
@jwt_required()
def recalculate_fees():
    """Recalculate fees based on updated container/weight information"""
    try:
        data = request.get_json()
        bill_id = data.get('bill_id')
        container_count = data.get('container_count')
        total_weight_kg = data.get('total_weight_kg')
        shipment_type = data.get('shipment_type', 'ocean')
        
        if not bill_id:
            return jsonify({'error': 'Bill ID is required'}), 400
        
        # Get pricing configuration
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get pricing based on shipment type
        cursor.execute("""
            SELECT ctn_fee_per_unit, service_fee_per_unit, unit_type, minimum_charge
            FROM pricing_config 
            WHERE shipment_type = %s AND is_active = TRUE
            ORDER BY container_type NULLS LAST
            LIMIT 1
        """, (shipment_type,))
        
        pricing = cursor.fetchone()
        
        if not pricing:
            # Fallback to default pricing
            ctn_fee_per_unit = 100.0
            service_fee_per_unit = 100.0
            unit_type = 'container'
            minimum_charge = 200.0
        else:
            ctn_fee_per_unit = float(pricing[0]) if pricing[0] else 100.0
            service_fee_per_unit = float(pricing[1]) if pricing[1] else 100.0
            unit_type = pricing[2] if pricing[2] else 'container'
            minimum_charge = float(pricing[3]) if pricing[3] else 200.0
        
        # Calculate fees based on unit type
        if unit_type == 'container' and container_count:
            ctn_fee = ctn_fee_per_unit * container_count
            service_fee = service_fee_per_unit * container_count
        elif unit_type == 'kg' and total_weight_kg:
            ctn_fee = ctn_fee_per_unit * total_weight_kg
            service_fee = service_fee_per_unit * total_weight_kg
        else:
            ctn_fee = ctn_fee_per_unit
            service_fee = service_fee_per_unit
        
        # Apply minimum charge
        total_fee = ctn_fee + service_fee
        if total_fee < minimum_charge:
            ratio = minimum_charge / total_fee if total_fee > 0 else 1
            ctn_fee *= ratio
            service_fee *= ratio
        
        # Update the bill with recalculated fees
        cursor.execute("""
            UPDATE bill_of_lading 
            SET calculated_ctn_fee = %s, calculated_service_fee = %s,
                container_count = %s, total_weight_kg = %s, shipment_type = %s
            WHERE id = %s
        """, (ctn_fee, service_fee, container_count, total_weight_kg, shipment_type, bill_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'calculated_ctn_fee': round(ctn_fee, 2),
            'calculated_service_fee': round(service_fee, 2),
            'total_fee': round(ctn_fee + service_fee, 2),
            'pricing_method': unit_type
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to recalculate fees: {str(e)}'}), 500

@bill_routes.route('/pricing_config', methods=['GET'])
@jwt_required()
def get_pricing_config():
    """Get current pricing configuration"""
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT shipment_type, container_type, pricing_method, 
                   ctn_fee_per_unit, service_fee_per_unit, unit_type, 
                   minimum_charge, maximum_charge, is_active, notes
            FROM pricing_config 
            WHERE is_active = TRUE
            ORDER BY shipment_type, container_type NULLS LAST
        """)
        
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        
        configs = []
        for row in rows:
            configs.append(dict(zip(columns, row)))
        
        cur.close()
        conn.close()
        
        return jsonify({'pricing_configs': configs})
        
    except Exception as e:
        return jsonify({'error': f'Error fetching pricing config: {str(e)}'}), 400