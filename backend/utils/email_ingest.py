def ingest_emails():

    import re
    import json
    from config import get_db_conn
    from datetime import datetime

    print("[DEBUG] Ingesting emails from inbox")
    # Example: emails = fetch_emails_from_inbox()
    emails = [
        {
            'from': 'customer@example.com',
            'subject': 'Test Email',
            'body': 'This is a test email mentioning BL12345.',
            'attachments': ['https://res.cloudinary.com/demo/image/upload/sample.pdf'],
            'date': datetime.now(),
        }
    ]
    conn = get_db_conn()
    cur = conn.cursor()
    for email in emails:
        # Parse B/L numbers from body (simple regex for BL numbers)
        bl_numbers = re.findall(r'BL\d+', email['body'])
        print(f"[DEBUG] Parsed B/L numbers: {bl_numbers} from email: {email['subject']}")
        cur.execute("""
            INSERT INTO customer_emails (sender, subject, body, attachments, bl_numbers, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            email['from'],
            email['subject'],
            email['body'],
            json.dumps(email['attachments']),
            bl_numbers,
            email['date']
        ))
        print(f"[DEBUG] Saved customer_email: {email['subject']} from {email['from']}")
    conn.commit()
    cur.close()
    conn.close()
    return []
