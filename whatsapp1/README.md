# WhatsApp Assistant for IQSTrade

This service connects to WhatsApp using Baileys, answers customer questions using OpenAI GPT-4o, and fetches invoice/CTN info from the shared Railway PostgreSQL database.

## Setup

1. Copy `.env` from the main iqstrade project or fill in the required variables:
   - `RAILWAY_DB_HOST`, `RAILWAY_DB_USER`, `RAILWAY_DB_PASSWORD`, `RAILWAY_DB_NAME`, `RAILWAY_DB_PORT`
   - `OPENAI_API_KEY` (GPT-4o or 4o-mini)
   - `ADMIN_WA_ID` (your WhatsApp number, e.g., whatsapp:+85212345678)
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the service:
   ```bash
   node index.js
   ```

## Key Files
- `index.js`: Entry point
- `whatsappClient.js`: Baileys WhatsApp connection
- `chatHandler.js`: OpenAI GPT logic
- `db.js`: PostgreSQL connection
- `messageRouter.js`: Message parsing/routing
- `test.js`: Simple test script

## Features
- Answers pricing, payment, invoice, and CTN questions
- Forwards all conversations to admin
- Secure, no secrets in code
- Ready for Render deployment

## Testing
Run the test script:
```bash
node test.js
``` 