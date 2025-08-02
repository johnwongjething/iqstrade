import os
import psycopg2
from dotenv import load_dotenv
from .log import logger

# Load env from ../iqstrade/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '../../iqstrade/.env'))

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

def upload_to_db(data):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        # Example: insert into bill_of_lading (customize as needed)
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO bill_of_lading ({columns}) VALUES ({placeholders})"
        cur.execute(sql, list(data.values()))
        conn.commit()
        logger.info(f"Inserted into DB: {data}")
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"DB upload error: {e}") 