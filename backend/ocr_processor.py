import sys
import os
import fitz  # PyMuPDF
import openai
import json
from dotenv import load_dotenv
import logging
import base64
from openai_config import OpenAIConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env from .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))
openai.api_key = os.getenv('OPENAI_API_KEY')

def openai_call_with_fallback(messages, temperature=0, max_tokens=None):
    """
    Make OpenAI API call with production fallback strategy
    OCR: GPT-4o → GPT-3.5-turbo (high accuracy for document processing)
    """
    # Get OCR-specific configuration
    ocr_config = OpenAIConfig.get_ocr_settings()
    
    # Check if the message contains image content
    has_image = False
    for message in messages:
        if isinstance(message.get('content'), list):
            for content_item in message['content']:
                if content_item.get('type') == 'image_url':
                    has_image = True
                    break
        if has_image:
            break
    
    # Use vision-capable models if image is present
    if has_image:
        models = [ocr_config['primary_model'], ocr_config['fallback_model']]
        # Ensure GPT-4o is used for vision tasks
        if 'gpt-4o' not in models:
            models = ['gpt-4o'] + [m for m in models if m != 'gpt-4o']
    else:
        models = [ocr_config['primary_model'], ocr_config['fallback_model']]
    
    for i, model in enumerate(models):
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens
                
            response = openai.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            logger.info(f"[OpenAI OCR] Successfully used {model} for OCR processing")
            return content
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "rate limit" in error_msg or "billing" in error_msg:
                if i < len(models) - 1:
                    logger.warning(f"[OpenAI OCR] {model} quota/rate limit exceeded, falling back to {models[i+1]}")
                    continue
                else:
                    logger.error(f"[OpenAI OCR] All models exhausted: {e}")
                    raise e
            else:
                logger.error(f"[OpenAI OCR] Error with {model}: {e}")
                raise e
    
    raise Exception("All OpenAI models failed")

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
        "For consignee extraction, look for 'CONSIGNED TO' or 'CONSIGNEE' sections and extract ONLY the company name (not the address). "
        "For container_numbers, look for patterns like 'OOCU7645789', 'TGBU8072614', etc. "
        "For flight_or_vessel, look for vessel names like 'OOCL BERLIN v.041E' or flight numbers. "
        "Return a valid JSON object with these fields. If a field is missing, use an empty string."
    )
    messages = [
        {"role": "system", "content": "You're an expert shipping document parser."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": vision_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]
        }
    ]
    vision_content = openai_call_with_fallback(messages, max_tokens=1024)
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

            # OpenAI Vision extracted fields
    return vision_data

def extract_fields_openai(pdf_path):
    logger.info(f"[OpenAI OCR] Extracting fields from: {pdf_path}")
    try:
        pdf = fitz.open(pdf_path)
        all_text = "\n".join(page.get_text() for page in pdf)
        
        # If text is empty, go straight to Vision
        if not all_text.strip():
            return call_openai_vision_fallback(pdf, all_text)

        prompt = f"""
You are an expert in logistics document processing. Given the following text from a shipping document, extract:
- document_type: (BOL or AWB)
- bl_number
- shipper
- consignee: Look for "CONSIGNED TO" or "CONSIGNEE" sections. Extract ONLY the company name (not the address). If you see "CONSIGNED TO" followed by a company name, that is the consignee. Do not include address information, phone numbers, or other details - just the company name.
- port_of_loading
- port_of_discharge
- container_numbers: Look for container numbers like "OOCU7645789", "TGBU8072614", etc. Extract all container numbers found.
- flight_or_vessel: Look for vessel names like "OOCL BERLIN v.041E" or flight numbers
- product_description
- paid_amount: the payment amount shown on the document (e.g., $420, 420 USD, Amount: 420, etc)

IMPORTANT: For consignee extraction, pay special attention to:
1. "CONSIGNED TO" sections - this is the primary consignee
2. "CONSIGNEE" sections
3. Company names that appear after these labels

TEXT:\n{all_text}

Return a valid JSON object with these fields. If a field is missing, use an empty string.
"""
        messages = [
            {"role": "system", "content": "You're an expert shipping document parser."},
            {"role": "user", "content": prompt},
        ]
        content = openai_call_with_fallback(messages, temperature=0.0)
        try:
            data = json.loads(content)
        except Exception:
            import re
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                except Exception:
                    return call_openai_vision_fallback(pdf, all_text)
            else:
                return call_openai_vision_fallback(pdf, all_text)

        data['raw_text'] = all_text
        for field in BILL_FIELDS:
            if field not in data:
                data[field] = ''
        if all(data.get(field, '') == '' for field in BILL_FIELDS if field != 'raw_text'):
            return call_openai_vision_fallback(pdf, all_text)
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