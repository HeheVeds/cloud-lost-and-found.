import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env if present
basedir = Path(__file__).resolve().parent.parent
load_dotenv(basedir / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_cloud_lost_and_found_2026")
    
    # Database Settings
    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
    USE_RDS = os.getenv("USE_RDS", "false").lower() in ("true", "1", "yes")
    DB_HOST = os.getenv("DB_HOST", "").strip()
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "lost_and_found_db")
    DB_USER = os.getenv("DB_USER", "admin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # 1. Direct Cloud Database URL (Neon / Supabase / Aiven / Render / TiDB)
    is_valid_cloud_db = (
        DATABASE_URL 
        and "://" in DATABASE_URL 
        and not DATABASE_URL.startswith("paste_")
        and not "your_" in DATABASE_URL
    )
    if is_valid_cloud_db:
        clean_url = DATABASE_URL
        if clean_url.startswith("postgres://"):
            clean_url = clean_url.replace("postgres://", "postgresql://", 1)
        # Strip channel_binding if present as it can cause connection handshake issues in some Linux environments
        clean_url = clean_url.replace("&channel_binding=require", "").replace("?channel_binding=require&", "?").replace("?channel_binding=require", "")
        SQLALCHEMY_DATABASE_URI = clean_url
        DB_ENGINE_TYPE = "Cloud Database (Managed PostgreSQL / Cloud SQL)"
    # 2. AWS RDS or standard MySQL via individual parameters
    elif USE_RDS or DB_HOST:
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        )
        DB_ENGINE_TYPE = "AWS RDS / MySQL (Cloud DB)"
    # 3. Local SQLite Fallback
    else:
        sqlite_path = basedir / "lost_and_found.db"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{sqlite_path}"
        DB_ENGINE_TYPE = "SQLite (Local Dev Fallback)"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cloud Storage Option 1: Cloudinary (100% Free Forever, No Credit Card)
    USE_CLOUDINARY = os.getenv("USE_CLOUDINARY", "false").lower() in ("true", "1", "yes")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

    # Cloud Storage Option 2: AWS S3
    USE_S3 = os.getenv("USE_S3", "false").lower() in ("true", "1", "yes")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")

    # Local Upload Folder for testing fallback
    UPLOAD_FOLDER = str(basedir / "app" / "static" / "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # Admin Registration Secret Key
    ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "ADMIN_CLOUD_2026")
