import json

def check_missing_fields(ocr_text_json):
    try:
        fields = json.loads(ocr_text_json) if isinstance(ocr_text_json, str) else ocr_text_json
    except:
        return ["OCR data unreadable"]

    required = ['shipper', 'consignee', 'port_of_loading', 'port_of_discharge', 'bl_number']
    missing = [field for field in required if not fields.get(field)]
    return missing
