import sys
import os
import fitz  # PyMuPDF
import openai
import json
from dotenv import load_dotenv
import logging
import base64

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env from .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
openai.api_key = os.getenv('OPENAI_API_KEY')

BILL_FIELDS = [
    'document_type', 'bl_number', 'shipper', 'consignee', 'port_of_loading',
    'port_of_discharge', 'container_numbers', 'flight_or_vessel', 'product_description', 'paid_amount', 'raw_text'
]

def get_first_line(value):
    if not value:
        return value
    # Prefer first line if multi-line
    if '\n' in value:
        return value.split('\n')[0].strip()
    # Otherwise, first part before comma
    if ',' in value:
        return value.split(',')[0].strip()
    return value.strip()

def call_openai_vision_fallback(pdf, all_text):
    import base64
    page = pdf[0]
    pix = page.get_pixmap()
    img_bytes = pix.tobytes("png")
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    vision_prompt = (
        "Extract the following fields from this shipping document image: "
        "document_type, bl_number, shipper, consignee, port_of_loading, "
        "port_of_discharge, container_numbers, flight_or_vessel, product_description, paid_amount. "
        "The paid_amount is the payment amount shown on the document (e.g., $420, 420 USD, Amount: 420, etc). "
        "Return a valid JSON object with these fields. If a field is missing, use an empty string."
    )
    vision_response = openai.chat.completions.create(
        model="gpt-4o",  # Updated to gpt-4o as vision-preview is deprecated
        messages=[
            {"role": "system", "content": "You're an expert shipping document parser."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": vision_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
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
    # Post-process shipper and consignee to only keep the first line or first part before comma
    vision_data['shipper'] = get_first_line(vision_data.get('shipper', ''))
    vision_data['consignee'] = get_first_line(vision_data.get('consignee', ''))
    print(f"[DEBUG] [OpenAI] extract_fields_openai returning Vision data: {vision_data}")
    logger.info(f"[OpenAI Vision] Extracted fields: {vision_data}")
    return vision_data

def extract_fields_openai(pdf_path):
    print(f"[DEBUG] [OpenAI] extract_fields_openai called with pdf_path: {pdf_path}")
    logger.info(f"[OpenAI OCR] Extracting fields from: {pdf_path}")
    try:
        pdf = fitz.open(pdf_path)
        all_text = "\n".join(page.get_text() for page in pdf)
        
        # If text is empty, go straight to Vision
        if not all_text.strip():
            print("[DEBUG] [OpenAI] No text extracted from PDF, falling back to Vision API directly.")
            return call_openai_vision_fallback(pdf, all_text)

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
- paid_amount: the payment amount shown on the document (e.g., $420, 420 USD, Amount: 420, etc)

TEXT:\n{all_text}

Return a valid JSON object with these fields. If a field is missing, use an empty string.
"""
        print("[DEBUG] [OpenAI] Calling openai.ChatCompletion.create for OCR...")
        response = openai.chat.completions.create(
            model="gpt-4o",
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
                except Exception:
                    print("[DEBUG] [OpenAI] Regex fallback failed, falling back to Vision API...")
                    return call_openai_vision_fallback(pdf, all_text)
            else:
                print("[DEBUG] [OpenAI] No JSON found in response, falling back to Vision API...")
                return call_openai_vision_fallback(pdf, all_text)

        data['raw_text'] = all_text
        for field in BILL_FIELDS:
            if field not in data:
                data[field] = ''
        if all(data.get(field, '') == '' for field in BILL_FIELDS if field != 'raw_text'):
            print("[DEBUG] [OpenAI] Text extraction returned all empty, falling back to Vision API...")
            return call_openai_vision_fallback(pdf, all_text)

        print(f"[DEBUG] [OpenAI] extract_fields_openai returning data: {data}")
        logger.info(f"[OpenAI OCR] Extracted fields: {data}")
        return data
    except Exception as e:
        logger.error(f"[OpenAI OCR] Error: {e}")
        return {field: '' for field in BILL_FIELDS}

def process_pdf(pdf_path, dry_run=False):
    """
    Process a PDF file using OpenAI OCR.
    This function is called by the email ingestor.
    """
    logger.info(f"[Process PDF] Processing: {pdf_path}")
    if dry_run:
        logger.info(f"[Process PDF] DRY RUN - would process: {pdf_path}")
        return None
    
    try:
        # Extract fields using OpenAI
        fields = extract_fields_openai(pdf_path)
        logger.info(f"[Process PDF] Extracted fields: {fields}")
        return fields
    except Exception as e:
        logger.error(f"[Process PDF] Error processing {pdf_path}: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr_processor.py <pdf_path>")
        sys.exit(1)
    pdf_path = sys.argv[1]
    result = extract_fields_openai(pdf_path)
    print(result) 