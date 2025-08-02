# OpenAI OCR & Email Ingestor for IQSTrade

This module provides:
- OpenAI-powered OCR for PDF documents
- Automated email ingestion and PDF processing
- Seamless integration with the iqstrade database

## Setup

1. Copy or symlink your `../iqstrade/.env` file, or set environment variables as shown in `.env.example`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run OCR on a PDF:
   ```bash
   python ocr_processor.py sample.pdf --dry-run
   ```
4. Run email ingestion:
   ```bash
   python email_ingestor.py
   ```

## Folder Structure
- `ocr_processor.py`: Main OCR script
- `email_ingestor.py`: Email-to-OCR pipeline
- `utils/`: Shared helpers (OpenAI, DB, PDF, logging)
- `logs/ocr.log`: All logs

## Integration
- Uses the same DB schema and env as iqstrade
- Extracted fields match `bill_of_lading` upload route
- Ready for later integration with main system

## Security
- No secrets in code
- All credentials loaded from env
- Logs are rotated and not committed to git

## Testing
- Use `--dry-run` to print output instead of DB insert
- Check logs in `logs/ocr.log` 