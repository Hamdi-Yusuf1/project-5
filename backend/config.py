import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Central application configuration.

    Reads values from environment variables where available, falling back
    to sensible local-development defaults so the project runs out of the
    box with `python app.py`.
    """

    # --- Core ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "authenchain-dev-secret-key-2024")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "authenchain-jwt-secret-key-2024")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)

    # --- Database ---
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "14041999")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "authenchain_db")

    # Falls back to a local SQLite file if MySQL isn't configured, so the
    # project still runs instantly for demo/grading purposes.
    USE_SQLITE_FALLBACK = os.environ.get("USE_SQLITE_FALLBACK", "false").lower() == "true"

    if USE_SQLITE_FALLBACK:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'authenchain.db')}"
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    IMAGE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "images")
    QR_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "qrcodes")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB

    # --- CORS ---
    CORS_ORIGINS = "*"
