import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    print("Connection successful!")
    conn.close()
except Exception as e:
    print("Connection failed:", e)