def ingest_emails():
    print("[DEBUG] Ingesting emails from inbox")
    print("[DEBUG] Parsing attachments and matching to DB")
    return [
        {
            "filename": "payment_receipt_ABC123.pdf",
            "reason": "No matching B/L number found in DB"
        }
    ]
