import sys
import os
import fitz  # PyMuPDF
import openai
import json
from dotenv import load_dotenv
from utils.log import logger
import base64

# Load env from ../iqstrade/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '../../iqstrade/.env'))
openai.api_key = os.getenv('OPENAI_API_KEY')

BILL_FIELDS = [
    'document_type', 'bl_number', 'shipper', 'consignee', 'port_of_loading',
    'port_of_discharge', 'container_numbers', 'flight_or_vessel', 'product_description', 'raw_text'
]

def call_openai_vision_fallback(pdf):
    import base64
    page = pdf[0]
    pix = page.get_pixmap()
    img_bytes = pix.tobytes("png")
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    vision_prompt = (
        "Extract the following fields from this shipping document image: "
        "document_type, bl_number, shipper, consignee, port_of_loading, "
        "port_of_discharge, container_numbers, flight_or_vessel, product_description. "
        "Return a valid JSON object with these fields. If a field is missing, use an empty string."
    )
    vision_response = openai.chat.completions.create(
        model="gpt-4-vision-preview",  # or "gpt-4o" if it supports images
        messages=[
            {"role": "system", "content": "You're an expert shipping document parser."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": vision_prompt},
                    {"type": "image_url", "image_url": f"data:image/png;base64,{img_b64}"}
                ]
            }
        ],
        max_tokens=1024,
    )
    vision_content = vision_response.choices[0].message.content
    try:
        vision_data = json.loads(vision_content)
    except Exception:
        import re
        match = re.search(r'\{.*\}', vision_content, re.DOTALL)
        if match:
            try:
                vision_data = json.loads(match.group(0))
            except Exception:
                logger.error(f"[OpenAI Vision] Could not parse JSON from response: {vision_content}")
                vision_data = {field: '' for field in BILL_FIELDS}
        else:
            logger.error(f"[OpenAI Vision] Could not parse JSON from response: {vision_content}")
            vision_data = {field: '' for field in BILL_FIELDS}
    vision_data['raw_text'] = '[OpenAI Vision fallback used]'
    for field in BILL_FIELDS:
        if field not in vision_data:
            vision_data[field] = ''
    print(f"[DEBUG] [OpenAI] extract_fields_openai returning Vision data: {vision_data}")
    logger.info(f"[OpenAI Vision] Extracted fields: {vision_data}")
    return vision_data


def extract_fields_openai(pdf_path):
    print(f"[DEBUG] [OpenAI] extract_fields_openai called with pdf_path: {pdf_path}")
    logger.info(f"[OpenAI OCR] Extracting fields from: {pdf_path}")
    try:
        pdf = fitz.open(pdf_path)
        all_text = ""
        for page in pdf:
            text = page.get_text()
            all_text += text + "\n"
        prompt = f"""
You are an expert in logistics document processing. Given the following text from a shipping document, extract:
- document_type: (BOL or AWB)
- bl_number
- shipper
- consignee
- port_of_loading
- port_of_discharge
- container_numbers
- flight_or_vessel
- product_description

TEXT:\n{all_text}

Return a valid JSON object with these fields. If a field is missing, use an empty string.
"""
        print("[DEBUG] [OpenAI] Calling openai.ChatCompletion.create for OCR...")
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're an expert shipping document parser."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        print("[DEBUG] [OpenAI] openai.ChatCompletion.create response received.")
        content = response.choices[0].message.content
        try:
            data = json.loads(content)
        except Exception:
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                    data['raw_text'] = all_text
                    for field in BILL_FIELDS:
                        if field not in data:
                            data[field] = ''
                    if all(data.get(field, '') == '' for field in BILL_FIELDS if field != 'raw_text'):
                        print("[DEBUG] [OpenAI] Regex fallback returned all empty, falling back to Vision API...")
                        return call_openai_vision_fallback(pdf)
                except Exception:
                    print("[DEBUG] [OpenAI] Regex fallback failed, falling back to Vision API...")
                    return call_openai_vision_fallback(pdf)
            else:
                print("[DEBUG] [OpenAI] No JSON found in response, falling back to Vision API...")
                return call_openai_vision_fallback(pdf)
        data['raw_text'] = all_text
        for field in BILL_FIELDS:
            if field not in data:
                data[field] = ''
        if all(data.get(field, '') == '' for field in BILL_FIELDS if field != 'raw_text'):
            print("[DEBUG] [OpenAI] Text extraction returned all empty, falling back to Vision API...")
            return call_openai_vision_fallback(pdf)
        print(f"[DEBUG] [OpenAI] extract_fields_openai returning data: {data}")
        logger.info(f"[OpenAI OCR] Extracted fields: {data}")
        return data
    except Exception as e:
        logger.error(f"[OpenAI OCR] Error: {e}")
        return {field: '' for field in BILL_FIELDS}

# Existing process_pdf can call extract_fields_openai

def process_pdf(pdf_path, dry_run=False):
    logger.info(f"Processing PDF: {pdf_path}")
    try:
        data = extract_fields_openai(pdf_path)
        logger.info(f"Extracted fields: {data}")
        if dry_run:
            print("[DRY RUN] Would upload:", data)
        else:
            from utils.db_uploader import upload_to_db
            upload_to_db(data)
            logger.info("Upload to DB complete.")
    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr_processor.py <pdf_path> [--dry-run]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    process_pdf(pdf_path, dry_run=dry_run) 