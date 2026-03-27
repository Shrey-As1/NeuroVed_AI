import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_change_me_in_production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///cognisync.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_PRESCRIPTIONS = os.path.join(os.getcwd(), "uploads", "prescriptions")
    UPLOAD_MEDICINES     = os.path.join(os.getcwd(), "uploads", "medicines")
    UPLOAD_ANALYZER      = os.path.join(os.getcwd(), "uploads", "analyzer")

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")