from flask import Blueprint, request, jsonify, make_response, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.security import encrypt_sensitive_data, decrypt_sensitive_data, validate_password
from config import get_db_conn  # Updated import
from utils.helpers import get_hk_date_range
from extract_fields import extract_fields  # Add this import
import os
import json
import pytz
from datetime import datetime
from email_utils import send_unique_number_email, send_invoice_email, send_simple_email
from invoice_utils import generate_invoice_pdf

bill_routes = Blueprint('bill_routes', __name__)

# Set UPLOAD_FOLDER to absolute path in backend/uploads
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))

# Bill and file-related endpoints
# /bills, /bill/<id>, /uploads/<filename>, /upload, /bill/<id>/upload_receipt, /bill/<id>/unique_number, /send_unique_number_email, /send_invoice_email, /bill/<id>/delete, /generate_payment_link/<id>, /bills/status/<status>, /bills/awaiting_bank_in

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
        SELECT id, customer_name, customer_email, customer_phone, pdf_filename, shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers,
               flight_or_vessel, product_description, service_fee, ctn_fee, payment_link, receipt_filename, status, invoice_filename, unique_number, created_at, receipt_uploaded_at, customer_username, customer_invoice, customer_packing_list
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
    cur.close()
    conn.close()
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
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure upload dir exists
    user = json.loads(get_jwt_identity())
    username = user['username']
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        bill_pdfs = request.files.getlist('bill_pdf')
        invoice_pdf = request.files.get('invoice_pdf')
        packing_pdf = request.files.get('packing_pdf')
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not phone:
            return jsonify({'error': 'Phone is required'}), 400
        if not bill_pdfs and not invoice_pdf and not packing_pdf:
            return jsonify({'error': 'At least one PDF file is required'}), 400
        def save_file_with_timestamp(file, label):
            if not file:
                return None, None
            now_str = datetime.now(pytz.timezone('Asia/Hong_Kong')).strftime('%Y-%m-%d_%H%M%S')
            filename = f"{now_str}_{label}_{file.filename}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            return filename, file_path
        uploaded_count = 0
        customer_invoice = None
        customer_packing_list = None
        if invoice_pdf:
            customer_invoice, _ = save_file_with_timestamp(invoice_pdf, 'invoice')
        if packing_pdf:
            customer_packing_list, _ = save_file_with_timestamp(packing_pdf, 'packing')
        if bill_pdfs:
            for bill_pdf in bill_pdfs:
                pdf_filename, pdf_path = save_file_with_timestamp(bill_pdf, 'bill')
                fields = {}
                if bill_pdf:
                    try:
                        fields = extract_fields(pdf_path)
                    except Exception as e:
                        fields = {}
                fields_json = json.dumps(fields)
                hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
                conn = get_db_conn()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO bill_of_lading (
                        customer_name, customer_email, customer_phone, pdf_filename, ocr_text,
                        shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers,
                        flight_or_vessel, product_description, status,
                        customer_username, created_at, customer_invoice, customer_packing_list
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    name, str(email), str(phone), pdf_filename, fields_json,
                    str(fields.get('shipper', '')),
                    str(fields.get('consignee', '')),
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
                    customer_packing_list
                ))
                conn.commit()
                cur.close()
                conn.close()
                uploaded_count += 1
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
        filename = f"receipt_{id}_{receipt.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        receipt.save(file_path)
        hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE bill_of_lading
            SET receipt_filename = %s, status = %s, receipt_uploaded_at = %s
            WHERE id = %s
        """, (filename, 'Awaiting Bank In', hk_now, id))
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
        # Determine PDF path
        if pdf_url and pdf_url.startswith('/uploads/'):
            pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', pdf_url.lstrip('/'))
        else:
            pdf_path = os.path.join(UPLOAD_FOLDER, bill.get('invoice_filename', ''))
        from email_utils import send_invoice_email as send_invoice_email_util
        success = send_invoice_email_util(to_email, subject, body, pdf_path)
        if success:
            # Update bill status to "Invoice Sent"
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

@bill_routes.route('/generate_payment_link/<int:id>', methods=['GET'])
@jwt_required()
def generate_payment_link(id):
    user = json.loads(get_jwt_identity())
    username = user['username']
    try:
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
        cur.close()
        conn.close()
        # Generate payment link logic here
        # For example, using a payment gateway API
        payment_link = f"https://payment-gateway.com/pay?amount={bill['service_fee']}&bill_id={id}"
        return jsonify({'payment_link': payment_link})
    except Exception as e:
        return jsonify({'error': f'Error generating payment link: {str(e)}'}), 400

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
            'payment_method', 'payment_status', 'reserve_status'
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
        try:
            customer = {
                'name': bill['customer_name'],
                'email': bill['customer_email'],
                'phone': bill['customer_phone']
            }
            invoice_filename = generate_invoice_pdf(customer, bill, bill.get('service_fee'), bill.get('ctn_fee'), bill.get('payment_link'))
            bill['invoice_filename'] = invoice_filename
        except Exception as e:
            print(f"Error generating invoice PDF: {str(e)}")
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
        print("DEBUG: start_date", start_date, "end_date", end_date)
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

# @bill_routes.route('/account_bills', methods=['GET'])
# @jwt_required()
# def account_bills():
#     from dateutil import parser
#     completed_at = request.args.get('completed_at')
#     bl_number = request.args.get('bl_number')
#     conn = get_db_conn()
#     cur = conn.cursor()
#     select_clause = '''
#         SELECT id, customer_name, customer_email, customer_phone, pdf_filename,
#                shipper, consignee, port_of_loading, port_of_discharge, bl_number,
#                container_numbers, service_fee, ctn_fee, payment_link, receipt_filename,
#                status, invoice_filename, unique_number, created_at, receipt_uploaded_at,
#                completed_at, allinpay_85_received_at,
#                customer_username, customer_invoice, customer_packing_list,
#                payment_method, payment_status, reserve_status
#         FROM bill_of_lading
#         WHERE status = 'Paid and CTN Valid'
#     '''
#     where_clauses = []
#     params = []
#     if completed_at:
#         start_date, end_date = get_hk_date_range(completed_at)
#         where_clauses.append(
#             "((payment_method = 'Allinpay' AND allinpay_85_received_at >= %s AND allinpay_85_received_at < %s) "
#             "OR (payment_method = 'Allinpay' AND completed_at >= %s AND completed_at < %s) "
#             "OR (payment_method != 'Allinpay' AND completed_at >= %s AND completed_at < %s))"
#         )
#         params.extend([start_date, end_date, start_date, end_date, start_date, end_date])
#     if bl_number:
#         where_clauses.append("bl_number ILIKE %s")
#         params.append(f'%{bl_number}%')
#     if where_clauses:
#         select_clause += " AND " + " AND ".join(where_clauses)
#     select_clause += " ORDER BY id DESC"
#     cur.execute(select_clause, tuple(params))
#     rows = cur.fetchall()
#     columns = [desc[0] for desc in cur.description]
#     bills = []
#     total_bank_ctn = 0
#     total_bank_service = 0
#     total_allinpay_85_ctn = 0
#     total_allinpay_85_service = 0
#     total_reserve_ctn = 0
#     total_reserve_service = 0
#     for row in rows:
#         bill = dict(zip(columns, row))
#         # Decrypt sensitive fields
#         if bill.get('customer_email'):
#             bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
#         if bill.get('customer_phone'):
#             bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])
#         try:
#             ctn_fee = float(bill.get('ctn_fee') or 0)
#             service_fee = float(bill.get('service_fee') or 0)
#         except (TypeError, ValueError):
#             ctn_fee = 0
#             service_fee = 0
#         # Default: show original values
#         bill['display_ctn_fee'] = ctn_fee
#         bill['display_service_fee'] = service_fee
#         # 85%/15% logic for Allinpay
#         is_85 = False
#         if bill.get('payment_method') == 'Allinpay':
#             allinpay_85_dt = bill.get('allinpay_85_received_at')
#             if allinpay_85_dt:
#                 if isinstance(allinpay_85_dt, str):
#                     try:
#                         allinpay_85_dt = parser.isoparse(allinpay_85_dt)
#                     except Exception:
#                         allinpay_85_dt = None
#                 if allinpay_85_dt and allinpay_85_dt.tzinfo is None:
#                     allinpay_85_dt = allinpay_85_dt.replace(tzinfo=pytz.UTC)
#                 if completed_at and allinpay_85_dt and start_date <= allinpay_85_dt < end_date:
#                     # Legacy logic: set per-row display to 85% for Allinpay 85% paid
#                     bill['display_ctn_fee'] = round(ctn_fee * 0.85, 2)
#                     bill['display_service_fee'] = round(service_fee * 0.85, 2)
#                     total_allinpay_85_ctn += bill['display_ctn_fee']
#                     total_allinpay_85_service += bill['display_service_fee']
#                     is_85 = True
#             reserve_status = (bill.get('reserve_status') or '').lower()
#             completed_dt = bill.get('completed_at')
#             if completed_dt:
#                 if isinstance(completed_dt, str):
#                     try:
#                         completed_dt = parser.isoparse(completed_dt)
#                     except Exception:
#                         completed_dt = None
#                 if completed_dt and completed_dt.tzinfo is None:
#                     completed_dt = completed_dt.replace(tzinfo=pytz.UTC)
#             if reserve_status in ['settled', 'reserve settled'] and completed_at and completed_dt and start_date <= completed_dt < end_date and not is_85:
#                 bill['display_ctn_fee'] = round(ctn_fee * 0.15, 2)
#                 bill['display_service_fee'] = round(service_fee * 0.15, 2)
#                 total_reserve_ctn += bill['display_ctn_fee']
#                 total_reserve_service += bill['display_service_fee']
#         else:
#             # Bank Transfer: always show full amount, but only count in summary if in date range
#             completed_dt = bill.get('completed_at')
#             if completed_dt:
#                 if isinstance(completed_dt, str):
#                     try:
#                         completed_dt = parser.isoparse(completed_dt)
#                     except Exception:
#                         completed_dt = None
#                 if completed_dt and completed_dt.tzinfo is None:
#                     completed_dt = completed_dt.replace(tzinfo=pytz.UTC)
#             if completed_at and completed_dt and start_date <= completed_dt < end_date:
#                 total_bank_ctn += bill['display_ctn_fee']
#                 total_bank_service += bill['display_service_fee']
#         bills.append(bill)
#     cur.close()
#     conn.close()
#     summary = {
#         'totalEntries': len(bills),
#         'totalCtnFee': round(total_bank_ctn + total_allinpay_85_ctn + total_reserve_ctn, 2),
#         'totalServiceFee': round(total_bank_service + total_allinpay_85_service + total_reserve_service, 2),
#         'bankTotal': round(total_bank_ctn + total_bank_service, 2),
#         'allinpay85Total': round(total_allinpay_85_ctn + total_allinpay_85_service, 2),
#         'reserveTotal': round(total_reserve_ctn + total_reserve_service, 2)
#     }
#     return jsonify({'bills': bills, 'summary': summary})

@bill_routes.route('/generate_payment_link/<int:id>', methods=['POST'])
@jwt_required()
def generate_payment_link_post(id):
    try:
        payment_link = f"https://pay.example.com/link/{id}"
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("UPDATE bill_of_lading SET payment_link = %s WHERE id = %s", (payment_link, id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"payment_link": payment_link})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bill_routes.route('/extract_fields', methods=['POST'])
@jwt_required()
def extract_fields_endpoint():
    """
    Expects a PDF file upload as 'pdf' in form-data.
    Returns extracted fields as JSON.
    """
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF file uploaded'}), 400
    pdf_file = request.files['pdf']
    temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{pdf_file.filename}")
    pdf_file.save(temp_path)
    try:
        fields = extract_fields(temp_path)
        os.remove(temp_path)
        return jsonify({'fields': fields})
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'error': f'OCR extraction failed: {str(e)}'}), 500
