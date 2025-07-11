from flask import Blueprint, request, jsonify
from config import get_db_conn
import logging
from datetime import datetime
import pytz
from app import limiter  # Import the limiter instance from app.py
from urllib.parse import urlencode
from flask_jwt_extended import jwt_required  # Import jwt_required

# Create a Blueprint for the payment link endpoint
payment_link = Blueprint('payment_link', __name__)

# Configure logging
logger = logging.getLogger(__name__)

# Rate limit: 5 requests per minute per IP address
@payment_link.route('/api/generate_payment_link/<int:bill_id>', methods=['POST'])
@limiter.limit("5 per minute")
@jwt_required()  # Require JWT authentication
def generate_payment_link(bill_id):
    """
    Generate a dummy payment link for a specific bill and store it in the database.
    Accepts optional parameters in the request body to customize the link.
    """
    
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        # Get data from the request body and print for debugging
        data = request.get_json()
        logger.info(f"[DEBUG] Payment link request data: {data}")
        amount = float(data.get('amount', 0.0))  # Default to 0.0 if not provided
        currency = data.get('currency', 'USD')  # Default to USD
        customer_email = data.get('customer_email')  # Optional, can be overridden
        description = data.get('description', 'Reserve Payment')  # Default description
        success_url = data.get('success_url', 'https://yourdomain.com/success')  # Default success URL
        cancel_url = data.get('cancel_url', 'https://yourdomain.com/cancel')  # Default cancel URL
        ctn_fee = float(data.get('ctn_fee', 0.0))  # Capture from input field
        service_fee = float(data.get('service_fee', 0.0))  # Capture from input field

        # Log the request
        logger.info(f"Generating payment link for bill_id {bill_id} with amount {amount} {currency}")

        # Fetch bill details (only customer_email and unique_number for now)
        cur.execute("""
            SELECT customer_email, unique_number
            FROM bill_of_lading
            WHERE id = %s
        """, (bill_id,))
        bill = cur.fetchone()

        if not bill:
            return jsonify({"error": "Bill not found"}), 404

        stored_email, unique_number = bill
        customer_email = customer_email or stored_email

        # Calculate reserve amount based on input fees
        reserve_amount = amount if amount > 0 else (ctn_fee + service_fee) * 0.15

        # Generate a dummy payment link using urlencode for safety
        hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        query_params = {
            'amount': f'{reserve_amount:.2f}',
            'currency': currency,
            'email': customer_email,
            'ctn': unique_number or 'None',
            'description': description,
            'success': success_url,
            'cancel': cancel_url,
            'timestamp': hk_now.strftime('%Y%m%d%H%M%S')
        }
        dummy_link = f"https://pay.dummy.com/link/{bill_id}?{urlencode(query_params)}"
        print(f"[DEBUG] Generated payment link: {dummy_link}")
        logger.info(f"[DEBUG] Generated payment link: {dummy_link}")

        # Update the database with the dummy payment link
        cur.execute("UPDATE bill_of_lading SET payment_link = %s WHERE id = %s", (dummy_link, bill_id))
        conn.commit()

        return jsonify({"payment_link": dummy_link})

    except Exception as e:
        logger.error(f"Failed to generate payment link for bill_id {bill_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
        conn.close()
