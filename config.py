import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
REGION_CODE = os.getenv("REGION_CODE", "IN")
DAILY_QUOTA_LIMIT = int(os.getenv("DAILY_QUOTA_LIMIT", 9000))
DATA_DIR = os.getenv("DATA_DIR", "data")

if not API_KEY:
    raise RuntimeError("YOUTUBE_API_KEY missing. Check your .env file.")