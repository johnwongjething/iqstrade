
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import csv
import io
import re
from config import get_db_conn
from email_utils import send_payment_confirmation_email
bank_routes = Blueprint('bank_routes', __name__)


@bank_routes.route("/admin/unmatched-receipts/<int:receipt_id>", methods=["DELETE"])
@jwt_required()
def delete_unmatched_receipt(receipt_id):
    conn = get_db_conn()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM bank_unmatched_records WHERE id = %s", (receipt_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Receipt not found"}), 404

    cursor.execute("DELETE FROM bank_unmatched_records WHERE id = %s", (receipt_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Deleted successfully"}), 200



def debug(msg):
    print(f"[BANK IMPORT DEBUG] {msg}")

@bank_routes.route('/admin/import-bank-statement', methods=['POST'])
def import_bank_statement():
    if 'file' not in request.files:
        return jsonify({"error": "No CSV file provided"}), 400

    file = request.files['file']
    if not file:
        return jsonify({"error": "Invalid file"}), 400

    debug("Received bank CSV file")

    content = file.read().decode('utf-8')


    content_io = io.StringIO(content)

    try:
            sniffed_dialect = csv.Sniffer().sniff(content_io.read(1024))
            content_io.seek(0)
            reader = csv.DictReader(content_io, dialect=sniffed_dialect)
            debug(f"[BANK IMPORT DEBUG] Detected CSV delimiter: {sniffed_dialect.delimiter}")
    except Exception as e:
            debug(f"[BANK IMPORT DEBUG] CSV sniffing failed ({e}). Falling back to default comma delimiter.")
            content_io.seek(0)
            reader = csv.DictReader(content_io)
    results = []

    conn = get_db_conn()
    cursor = conn.cursor()

    for row in reader:
        date = row.get('Date', '')
        description = row.get('Description', '')
        amount_str = row.get('Amount', '').replace('$', '').replace(',', '').strip()
        try:
            amount = float(amount_str)
        except:
            debug(f"Invalid amount in row: {row}")
            continue

        debug(f"Processing row: Date={date}, Desc={description}, Amount={amount}")

        # Extract possible BL Numbers
        bl_numbers = set()
        bl_numbers.update(re.findall(r'\b[A-Z]{3}\d{6,}\b', description))
        bl_numbers.update(re.findall(r'\bBL[ -]?[0-9]{4,}\b', description, re.IGNORECASE))

        if not bl_numbers:
            debug("No BL number detected, logging as unmatched")
            cursor.execute("""
                INSERT INTO bank_unmatched_records (date, description, amount, reason)
                VALUES (%s, %s, %s, %s)
            """, (date, description, amount, 'No BL number detected'))
            results.append({
                "status": "Unmatched",
                "description": description,
                "amount": amount,
                "reason": "No BL number detected"
            })
            continue

        matched_any = False

        for bl in bl_numbers:
            debug(f"Attempting match for BL: {bl}")

            cursor.execute("""
                SELECT id, ctn_fee, service_fee, customer_email, customer_name
                FROM bill_of_lading
                WHERE bl_number = %s AND status != 'Paid'
            """, (bl,))
            bill = cursor.fetchone()

            if bill:
                bl_id, ctn_fee, service_fee, customer_email, customer_name = bill
                ctn_fee = float(ctn_fee) if ctn_fee else 0
                service_fee = float(service_fee) if service_fee else 0
                expected = ctn_fee + service_fee

                if abs(expected - amount) <= 2.0:
                    debug(f"Match found for BL {bl_id}. Marking as Paid.")

                    cursor.execute("""
                        UPDATE bill_of_lading
                        SET status = 'Paid and CTN Valid', payment_reference = %s
                        WHERE id = %s
                    """, (description, bl_id))
                    conn.commit()

                    try:
                        send_payment_confirmation_email(customer_email, customer_name, bl)
                        debug(f"Sent payment confirmation email to {customer_email}")
                    except Exception as e:
                        debug(f"Email sending failed: {e}")

                    matched_any = True
                    results.append({"bl_number": bl, "status": "Matched and marked Paid"})
                else:
                    debug(f"Amount mismatch. Expected: {expected}, Received: {amount}")
                    cursor.execute("""
                        INSERT INTO bank_unmatched_records (date, description, amount, reason)
                        VALUES (%s, %s, %s, %s)
                    """, (date, description, amount, f'Amount mismatch for BL {bl}'))
                    results.append({
                        "bl_number": bl,
                        "status": "Unmatched",
                        "description": description,
                        "amount": amount,
                        "reason": f'Amount mismatch for BL {bl}'
                    })
            else:
                debug(f"No unpaid record for BL {bl}. Logging as unmatched.")
                cursor.execute("""
                    INSERT INTO bank_unmatched_records (date, description, amount, reason)
                    VALUES (%s, %s, %s, %s)
                """, (date, description, amount, f'No unpaid record for BL {bl}'))
                conn.commit()
                results.append({
                    "bl_number": bl,
                    "status": "Unmatched",
                    "description": description,
                    "amount": amount,
                    "reason": f'No unpaid record for BL {bl}'
                })

        # Remove the commit here, as unmatched records are now committed above

    cursor.close()
    conn.close()

    return jsonify({"message": "Bank statement processed", "results": results})

# @bank_routes.route('/admin/bank-unmatched', methods=['GET'])
# def get_unmatched_records():
#     conn = get_db_conn()
#     cursor = conn.cursor()
#     cursor.execute("""
#         SELECT id, date, description, amount, reason, created_at
#         FROM bank_unmatched_records
#         ORDER BY created_at DESC
#         LIMIT 100
#     """)
#     rows = cursor.fetchall()
#     results = [
#         {
#             "id": row[0],
#             "date": row[1],
#             "description": row[2],
#             "amount": float(row[3]),
#             "reason": row[4],
#             "created_at": row[5].isoformat()
#         }
#         for row in rows
#     ]
#     cursor.close()
#     conn.close()
#     return jsonify(results)

@bank_routes.route('/admin/unmatched-receipts', methods=['GET'])
@jwt_required()
def get_unmatched_records():
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, date, description, amount, reason, created_at
        FROM bank_unmatched_records
        ORDER BY created_at DESC
        LIMIT 100
    """)
    rows = cursor.fetchall()
    print(f"[DEBUG] Unmatched receipts fetched: {rows}")
    results = [
        {
            "id": row[0],
            "date": row[1],
            "description": row[2],
            "amount": float(row[3]),
            "reason": row[4],
            "created_at": row[5].isoformat()
        }
        for row in rows
    ]
    print(f"[DEBUG] Unmatched receipts results: {results}")
    cursor.close()
    conn.close()
    return jsonify(results)
