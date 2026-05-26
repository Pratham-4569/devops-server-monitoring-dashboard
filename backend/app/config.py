import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    CPU_THRESHOLD = int(os.environ.get("CPU_THRESHOLD", "80"))
    RAM_THRESHOLD = int(os.environ.get("RAM_THRESHOLD", "85"))
    DISK_THRESHOLD = int(os.environ.get("DISK_THRESHOLD", "90"))
    POLL_INTERVAL_MS = int(os.environ.get("POLL_INTERVAL_MS", "3000"))
