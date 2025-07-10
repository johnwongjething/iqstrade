from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.security import decrypt_sensitive_data
from config import get_db_conn  # Updated import
from utils.helpers import get_hk_date_range
import pytz
from datetime import datetime
import json

stats_routes = Blueprint('stats_routes', __name__)

@stats_routes.route('/stats/files_by_date')
@jwt_required()
def files_by_date():
    user = get_jwt_identity()
    if user and json.loads(user).get('role') != 'staff':
        return jsonify({'error': 'Unauthorized'}), 403
    query_date = request.args.get('date')
    conn = get_db_conn()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cur = conn.cursor()
    start_date, end_date = get_hk_date_range(query_date)
    cur.execute("SELECT COUNT(*) FROM bill_of_lading WHERE created_at >= %s AND created_at < %s", (start_date, end_date))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return jsonify({'files_created': count})

@stats_routes.route('/stats/completed_today')
@jwt_required()
def completed_today():
    user = get_jwt_identity()
    if user and json.loads(user).get('role') != 'staff':
        return jsonify({'error': 'Unauthorized'}), 403
    hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
    today = hk_now.date().isoformat()
    conn = get_db_conn()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cur = conn.cursor()
    start_date, end_date = get_hk_date_range(today)
    cur.execute("SELECT COUNT(*) FROM bill_of_lading WHERE status='Completed' AND completed_at >= %s AND completed_at < %s", (start_date, end_date))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return jsonify({'completed_today': count})

@stats_routes.route('/stats/payments_by_date')
@jwt_required()
def payments_by_date():
    user = get_jwt_identity()
    if user and json.loads(user).get('role') != 'staff':
        return jsonify({'error': 'Unauthorized'}), 403
    query_date = request.args.get('date')
    conn = get_db_conn()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cur = conn.cursor()
    start_date, end_date = get_hk_date_range(query_date)
    cur.execute("SELECT SUM(service_fee) FROM bill_of_lading WHERE created_at >= %s AND created_at < %s", (start_date, end_date))
    total = cur.fetchone()[0] or 0
    cur.close()
    conn.close()
    return jsonify({'payments_received': float(total)})

@stats_routes.route('/stats/bills_by_date')
@jwt_required()
def bills_by_date():
    user = get_jwt_identity()
    if user and json.loads(user).get('role') != 'staff':
        return jsonify({'error': 'Unauthorized'}), 403
    query_date = request.args.get('date')
    conn = get_db_conn()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cur = conn.cursor()
    start_date, end_date = get_hk_date_range(query_date)
    cur.execute("""
        SELECT 
            COUNT(*) as total_entries,
            COALESCE(SUM(ctn_fee), 0) as total_ctn_fee,
            COALESCE(SUM(service_fee), 0) as total_service_fee
        FROM bill_of_lading 
        WHERE created_at >= %s AND created_at < %s
    """, (start_date, end_date))
    summary = cur.fetchone()
    cur.execute("""
        SELECT 
            id, customer_name, customer_email, 
            ctn_fee, service_fee, 
            COALESCE(ctn_fee + service_fee, 0) as total,
            created_at
        FROM bill_of_lading 
        WHERE created_at >= %s AND created_at < %s
        ORDER BY created_at DESC
    """, (start_date, end_date))
    entries = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify({
        'summary': {
            'total_entries': summary[0],
            'total_ctn_fee': float(summary[1]),
            'total_service_fee': float(summary[2])
        },
        'entries': entries
    })

@stats_routes.route('/stats/summary')
@jwt_required()
def stats_summary():
    user = get_jwt_identity()
    if user and json.loads(user).get('role') not in ['staff', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_conn()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM bill_of_lading")
    total_bills = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM bill_of_lading WHERE status = 'Paid and CTN Valid'")
    completed_bills = cur.fetchone()[0]
    cur.execute("""
    SELECT COUNT(*) 
    FROM bill_of_lading 
    WHERE status IN ('Pending', 'Invoice Sent', 'Awaiting Bank In')
    """)
    pending_bills = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(ctn_fee + service_fee), 0) FROM bill_of_lading")
    total_invoice_amount = float(cur.fetchone()[0] or 0)
    cur.execute("""
        SELECT COALESCE(SUM(
            CASE 
                WHEN payment_method != 'Allinpay' AND status = 'Paid and CTN Valid'
                    THEN ctn_fee + service_fee
                WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Reserve Settled'
                    THEN ctn_fee + service_fee
                WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Unsettled'
                    THEN (ctn_fee * 0.85) + (service_fee * 0.85)
                ELSE 0
            END
        ), 0)
        FROM bill_of_lading
    """)
    total_payment_received = float(cur.fetchone()[0] or 0)
    cur.execute("""
    SELECT COALESCE(SUM(service_fee + ctn_fee), 0)
    FROM bill_of_lading
    WHERE status IN ('Awaiting Bank In', 'Invoice Sent')
    """)
    awaiting_payment = float(cur.fetchone()[0] or 0)
    cur.execute("SELECT COALESCE(SUM(reserve_amount), 0) FROM bill_of_lading WHERE LOWER(TRIM(reserve_status)) = 'unsettled'")
    unsettled_reserve = float(cur.fetchone()[0] or 0)
    total_payment_outstanding = awaiting_payment + unsettled_reserve
    cur.close()
    conn.close()
    return jsonify({
        'total_bills': total_bills,
        'completed_bills': completed_bills,
        'pending_bills': pending_bills,
        'total_invoice_amount': round(total_invoice_amount, 2),
        'total_payment_received': round(total_payment_received, 2),
        'total_payment_outstanding': round(total_payment_outstanding, 2)
    })

@stats_routes.route('/stats/outstanding_bills')
@jwt_required()
def outstanding_bills():
    user = get_jwt_identity()
    if user and json.loads(user).get('role') not in ['staff', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_conn()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            id, customer_name, bl_number,
            ctn_fee, service_fee, reserve_amount,
            payment_method, reserve_status, invoice_filename
        FROM bill_of_lading
        WHERE status IN ('Awaiting Bank In', 'Invoice Sent')
           OR (payment_method = 'Allinpay' AND LOWER(TRIM(reserve_status)) = 'unsettled')
    """)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    bills = []
    for row in rows:
        bill = dict(zip(columns, row))
        ctn_fee = float(bill.get('ctn_fee') or 0)
        service_fee = float(bill.get('service_fee') or 0)
        payment_method = str(bill.get('payment_method') or '').strip().lower()
        reserve_status = str(bill.get('reserve_status') or '').strip().lower()
        outstanding_amount = round(ctn_fee + service_fee, 2)
        if payment_method == 'allinpay' and reserve_status == 'unsettled':
            outstanding_amount = round(ctn_fee * 0.15 + service_fee * 0.15, 2)
        bill['outstanding_amount'] = outstanding_amount
        bills.append(bill)
    cur.close()
    conn.close()
    return jsonify(bills)
