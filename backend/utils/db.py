from config import get_db_conn

def find_invoice_info(bl_numbers):
    """
    Accepts a single BL number (string) or a list of BL numbers.
    Returns a list of dicts with invoice info for each found BL.
    """
    if isinstance(bl_numbers, str):
        bl_numbers = [bl_numbers]
    conn = get_db_conn()
    cur = conn.cursor()
    results = []
    for bl in bl_numbers:
        cur.execute("""
            SELECT bl_number, invoice_filename, customer_name, service_fee, ctn_fee, payment_link
            FROM bill_of_lading
            WHERE bl_number = %s
            ORDER BY id DESC
            LIMIT 1
        """, (bl,))
        row = cur.fetchone()
        if row:
            results.append({
                "bl_number": row[0],
                "invoice_filename": row[1],
                "customer_name": row[2],
                "service_fee": row[3],
                "ctn_fee": row[4],
                "payment_link": row[5]
            })
    cur.close()
    conn.close()
    return results 