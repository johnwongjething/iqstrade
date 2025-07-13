from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from config import get_db_conn
from utils.ocr_checker import check_missing_fields
from utils.email_ingest import ingest_emails
import datetime
from datetime import timezone

management_routes = Blueprint('management_routes', __name__)

@management_routes.route('/management/overview', methods=['GET'])
@jwt_required()
def management_overview():
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        print("[DEBUG] Fetching B/L records...")
        cur.execute("""
            SELECT id, customer_name, bl_number, status, created_at,
                   invoice_filename, receipt_filename, ocr_text, ctn_fee, service_fee,
                   shipper, consignee, port_of_loading, port_of_discharge, flight_or_vessel, container_numbers
            FROM bill_of_lading
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        bills = []
        now = datetime.datetime.now(timezone.utc)
        print("[DEBUG] Processing bills...")
        for row in rows:
            bill = dict(zip(columns, row))
            created_at = bill.get("created_at")
            status = bill.get("status")
            ctn_fee = bill.get("ctn_fee") or 0
            service_fee = bill.get("service_fee") or 0
            paid_amount = 0  # Column does not exist, set to 0
            # Calculate flags
            is_new = False
            is_overdue = False
            if created_at:
                if isinstance(created_at, str):
                    created_at_dt = datetime.datetime.fromisoformat(created_at)
                else:
                    created_at_dt = created_at
                delta = now - created_at_dt.replace(tzinfo=timezone.utc)
                is_new = delta.total_seconds() < 86400
                is_overdue = status in ["Pending", "Awaiting Bank In"] and delta.total_seconds() > 604800
            total_invoice_amount = ctn_fee + service_fee
            bill["is_new"] = is_new
            bill["is_overdue"] = is_overdue
            bill["total_invoice_amount"] = total_invoice_amount
            bills.append(bill)

        print(f"[DEBUG] Processed {len(bills)} bills.")

        # Metrics
        print("[DEBUG] Calculating metrics...")
        total_bills = len(bills)
        pending_bills = sum(1 for b in bills if b.get("status") == "Pending")
        awaiting_bank_in = sum(1 for b in bills if b.get("status") == "Awaiting Bank In")
        completed_bills = sum(1 for b in bills if b.get("status") == "Completed")
        paid_bills = sum(1 for b in bills if b.get("status") == "Paid")
        sum_invoice_amount = sum(b.get("total_invoice_amount", 0) for b in bills)
        sum_paid_amount = sum(b.get("paid_amount", 0) for b in bills)
        sum_outstanding_amount = sum(b.get("total_invoice_amount", 0) - b.get("paid_amount", 0) for b in bills)

        metrics = {
            "total_bills": total_bills,
            "pending_bills": pending_bills,
            "awaiting_bank_in": awaiting_bank_in,
            "completed_bills": completed_bills,
            "paid_bills": paid_bills,
            "sum_invoice_amount": sum_invoice_amount,
            "sum_paid_amount": sum_paid_amount,
            "sum_outstanding_amount": sum_outstanding_amount
        }
        print(f"[DEBUG] Metrics: {metrics}")

        flagged_ocr = []
        print("[DEBUG] Checking missing required fields from DB columns...")
        required_fields = [
            "shipper", "consignee", "port_of_loading", "port_of_discharge", "bl_number", "flight_or_vessel", "container_numbers"
        ]
        for b in bills:
            missing = [field for field in required_fields if not b.get(field)]
            # Only show if at least one required field is empty/null
            if missing and len(missing) > 0:
                flagged_ocr.append({"id": b["id"], "bl_number": b["bl_number"], "missing": missing})

        print("[DEBUG] Ingesting unmatched receipts...")
        unmatched_receipts_raw = ingest_emails()
        unmatched_receipts = []
        # Try to extract BL number from filename or add as None if not found
        for receipt in unmatched_receipts_raw:
            bl_number = None
            # Example: try to extract BL number from filename if pattern exists
            filename = receipt.get("filename", "")
            # If filename contains BL number, extract it (customize pattern as needed)
            # Example: payment_receipt_<BLNUMBER>.pdf
            import re
            match = re.search(r"([A-Z0-9]+)", filename)
            if match:
                bl_number = match.group(1)
            receipt["bl_number"] = bl_number
            unmatched_receipts.append(receipt)

        print("[DEBUG] Returning overview response...")
        return jsonify({
            "bills": bills,
            "flags": {
                "ocr_missing": flagged_ocr,
                "unmatched_receipts": unmatched_receipts
            },
            "metrics": metrics
        })

    except Exception as e:
        print("[ERROR] Management dashboard error:", e)
        return jsonify({"error": str(e)}), 500
