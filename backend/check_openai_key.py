
import os
from dotenv import load_dotenv

# Try loading .env.local
env_path = os.path.join(os.path.dirname(__file__), '.env.local')
if os.path.exists(env_path):
    print(f"Loading .env.local from {env_path}")
    load_dotenv(env_path)
else:
    print(".env.local not found")

key = os.getenv('OPENAI_API_KEY')
if key:
    print(f"OPENAI_API_KEY is set. Length: {len(key)}")
    print(f"Starts with: {key[:7]}...")
else:
    print("OPENAI_API_KEY is NOT set.")
