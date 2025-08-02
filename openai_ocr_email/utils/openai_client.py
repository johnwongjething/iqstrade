import os
import openai
from dotenv import load_dotenv
from .log import logger

# Load env from ../iqstrade/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '../../iqstrade/.env'))

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

def extract_text_from_image(image_bytes):
    try:
        # Placeholder for OpenAI Vision API call
        # Replace with actual API call when available
        logger.info("Calling OpenAI Vision API...")
        # result = openai.vision.extract_text(image_bytes)
        # return result['text']
        return "[MOCKED] Extracted text from image"
    except Exception as e:
        logger.error(f"OpenAI Vision error: {e}")
        return "" 