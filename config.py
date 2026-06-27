"""
config.py
Central configuration for the Smart Vehicle Compliance & Automated Parking
Management System. Reads sensitive values from environment variables where
possible, with sane local-dev defaults so the app runs out of the box.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # --- Database ---
    # SQLite by default. Swap SQLALCHEMY_DATABASE_URI to a MySQL URI
    # (e.g. "mysql+pymysql://user:pass@localhost/smart_parking") to migrate.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database', 'parking.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "bmp"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB upload cap

    # --- Reports ---
    REPORTS_FOLDER = os.path.join(BASE_DIR, "reports")

    # --- OCR ---
    OCR_SAMPLE_FOLDER = os.path.join(BASE_DIR, "ocr", "sample_images")
    OCR_LANGUAGES = ["en"]
    OCR_GPU = False  # CPU-only by default for portability on student laptops

    # --- Parking business rules ---
    PARKING_RATE_PER_HOUR = 20.0  # INR per hour (simulated)
    MIN_CHARGE = 10.0             # minimum charge even for very short stays
    COMPLIANCE_WARNING_DAYS = 30  # "expiring soon" window

    # --- Session / security ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = None


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
