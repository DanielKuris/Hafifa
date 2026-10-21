import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

MAX_CONCURRENT_PAGES = int(os.getenv("MAX_CONCURRENT_PAGES", "5"))
NAVIGATION_TIMEOUT_MS = int(os.getenv("NAVIGATION_TIMEOUT_MS", "30000"))

INPUT_FILE = BASE_DIR / os.getenv("INPUT_FILE", "urls.input")
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")

BROWSER_CHANNEL = os.getenv("BROWSER_CHANNEL", "chrome")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
