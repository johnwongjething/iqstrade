# GSA System Backend Starter

This folder is the starting point for your Flask backend API for the GSA ticketing system.

## Structure
- `app.py` — Main Flask app entry point
- `models/` — SQLAlchemy models for all tables (users, agencies, flights, etc.)
- `routes/` — API route blueprints (auth, flights, bookings, payments, etc.)
- `config.py` — Configuration (database URI, secrets)
- `requirements.txt` — Python dependencies

## Next Steps
1. Set up your virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
2. Configure your database connection in `config.py`.
3. Implement models in `models/` based on the schema in `../db/GSA_DB_SCHEMA_STARTER.sql`.
4. Build out API endpoints in `routes/` for each module.
5. Add authentication, RBAC, and audit logging.
6. Test locally and iterate!

---

This backend is designed to be modular and easy to extend as your business grows. 