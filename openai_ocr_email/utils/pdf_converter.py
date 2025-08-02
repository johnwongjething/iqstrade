import fitz  # PyMuPDF
from .log import logger

def convert_pdf_to_images(pdf_path):
    images = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img_bytes = pix.tobytes()
            images.append(img_bytes)
        logger.info(f"Converted {pdf_path} to {len(images)} images")
    except Exception as e:
        logger.error(f"PDF conversion error: {e}")
    return images 