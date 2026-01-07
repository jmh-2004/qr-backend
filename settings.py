import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")

AUTH_MODE = os.getenv("AUTH_MODE", "DEV").upper()  # DEV or FIREBASE
FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT", "")

PAYOUT_PER_VALID_SCAN_USD = float(os.getenv("PAYOUT_PER_VALID_SCAN_USD", "0.001"))
