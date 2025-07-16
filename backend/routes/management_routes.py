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
            is_new = delta.total_seconds() < 86400 and status != "Invoice Sent"
            is_overdue = status in ["Pending", "Awaiting Bank In"] and delta.total_seconds() > 604800
            total_invoice_amount = ctn_fee + service_fee
            bill["is_new"] = is_new
            bill["is_overdue"] = is_overdue
            bill["total_invoice_amount"] = total_invoice_amount
            bills.append(bill)

        print(f"[DEBUG] Processed {len(bills)} bills.")


        # --- Begin: StaffStats.js/stats_summary logic copy ---
        print("[DEBUG] Calculating metrics (copied from stats_summary logic)...")
        total_bills = len(bills)
        pending_bills = sum(1 for b in bills if b.get("status") in ("Pending", "Invoice Sent", "Awaiting Bank In"))
        awaiting_bank_in = sum(1 for b in bills if b.get("status") == "Awaiting Bank In")

        completed_bills = sum(1 for b in bills if b.get("status") == "Paid and CTN Valid")
        sum_invoice_amount = sum((b.get("ctn_fee") or 0) + (b.get("service_fee") or 0) for b in bills)

        # Paid and outstanding logic (Allinpay/85%/reserve_status)
        sum_paid_amount = 0.0
        sum_outstanding_amount = 0.0
        for b in bills:
            ctn_fee = float(b.get("ctn_fee") or 0)
            service_fee = float(b.get("service_fee") or 0)
            invoice_amount = ctn_fee + service_fee
            payment_method = str(b.get("payment_method") or '').strip().lower()
            reserve_status = str(b.get("reserve_status") or '').strip().lower()
            status = b.get("status", "")
            # Paid logic
            if payment_method != 'allinpay' and status == 'Paid and CTN Valid':
                sum_paid_amount += invoice_amount
            elif payment_method == 'allinpay' and status == 'Paid and CTN Valid' and reserve_status == 'reserve settled':
                sum_paid_amount += invoice_amount
            elif payment_method == 'allinpay' and status == 'Paid and CTN Valid' and reserve_status == 'unsettled':
                sum_paid_amount += (ctn_fee * 0.85) + (service_fee * 0.85)
            # Outstanding logic
            if status in ('Awaiting Bank In', 'Invoice Sent'):
                sum_outstanding_amount += invoice_amount
            elif payment_method == 'allinpay' and reserve_status == 'unsettled':
                sum_outstanding_amount += (ctn_fee * 0.15) + (service_fee * 0.15)

        metrics = {
            "total_bills": total_bills,
            "pending_bills": pending_bills,
            "awaiting_bank_in": awaiting_bank_in,
            "completed_bills": completed_bills,
            "paid_bills": completed_bills,  # For consistency with previous logic
            "sum_invoice_amount": round(sum_invoice_amount, 2),
            "sum_paid_amount": round(sum_paid_amount, 2),
            "sum_outstanding_amount": round(sum_outstanding_amount, 2)
        }
        print(f"[DEBUG] Metrics: {metrics}")
        # --- End: StaffStats.js/stats_summary logic copy ---


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
