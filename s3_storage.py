import os
import uuid
import mimetypes
from pathlib import Path
from werkzeug.utils import secure_filename
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from flask import current_app

def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed image extension."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]

def is_s3_configured() -> bool:
    """Return True if AWS S3 settings are enabled and bucket is set."""
    cfg = current_app.config
    return bool(cfg.get("USE_S3") and cfg.get("S3_BUCKET_NAME"))

def get_s3_client():
    """Create and return a boto3 S3 client."""
    cfg = current_app.config
    aws_access_key = cfg.get("AWS_ACCESS_KEY_ID")
    aws_secret_key = cfg.get("AWS_SECRET_ACCESS_KEY")
    region = cfg.get("AWS_REGION", "us-east-1")

    # If keys are explicitly provided in environment
    if aws_access_key and aws_secret_key:
        return boto3.client(
            "s3",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
    # If deployed on AWS EC2 with an attached IAM Role, boto3 auto-discovers credentials
    return boto3.client("s3", region_name=region)

def upload_file_to_s3(file_storage, filename: str) -> tuple[str, str]:
    """
    Upload an item photograph to Amazon S3.
    Returns: (image_url, storage_provider_name)
    """
    cfg = current_app.config
    bucket = cfg["S3_BUCKET_NAME"]
    region = cfg["AWS_REGION"]

    s3_client = get_s3_client()
    content_type, _ = mimetypes.guess_type(filename)
    if not content_type:
        content_type = "image/jpeg"

    # Rewind file stream to beginning
    file_storage.seek(0)

    extra_args = {
        "ContentType": content_type
    }

    try:
        # Upload object to S3
        s3_client.upload_fileobj(
            file_storage,
            bucket,
            filename,
            ExtraArgs=extra_args
        )
        
        # Build direct S3 URL
        # Format for us-east-1 vs other regions
        if region == "us-east-1":
            s3_url = f"https://{bucket}.s3.amazonaws.com/{filename}"
        else:
            s3_url = f"https://{bucket}.s3.{region}.amazonaws.com/{filename}"
            
        print(f"[AWS S3] Successfully uploaded '{filename}' to S3 bucket '{bucket}'")
        return s3_url, "AWS S3"

    except (ClientError, NoCredentialsError) as e:
        print(f"[AWS S3 ERROR] Failed to upload to S3: {str(e)}. Falling back to local storage.")
        raise e

def is_cloudinary_configured() -> bool:
    """Return True if Cloudinary settings are enabled and configured."""
    cfg = current_app.config
    return bool(cfg.get("USE_CLOUDINARY") and cfg.get("CLOUDINARY_CLOUD_NAME"))

def upload_file_to_cloudinary(file_storage, filename: str) -> tuple[str, str]:
    """Upload an item photograph to Cloudinary free cloud storage."""
    import cloudinary
    import cloudinary.uploader
    cfg = current_app.config
    cloudinary.config(
        cloud_name=cfg["CLOUDINARY_CLOUD_NAME"],
        api_key=cfg["CLOUDINARY_API_KEY"],
        api_secret=cfg["CLOUDINARY_API_SECRET"],
        secure=True
    )
    file_storage.seek(0)
    base_id = filename.rsplit(".", 1)[0]
    res = cloudinary.uploader.upload(file_storage, public_id=base_id, folder="lost_and_found")
    cloud_url = res.get("secure_url")
    print(f"[CLOUDINARY] Uploaded successfully: {cloud_url}")
    return cloud_url, "Cloud Storage (Cloudinary)"

def save_image_file(file_storage) -> tuple[str | None, str]:
    """
    Save image file to Cloud (Cloudinary or AWS S3), or fallback to local disk.
    Returns (url_or_path, storage_engine_label)
    """
    if not file_storage or not file_storage.filename or file_storage.filename.strip() == "":
        return None, "None"

    if not allowed_file(file_storage.filename):
        return None, "Invalid File Type"

    # Generate unique, collision-free filename
    orig_name = secure_filename(file_storage.filename)
    extension = orig_name.rsplit(".", 1)[1].lower() if "." in orig_name else "jpg"
    unique_name = f"item_{uuid.uuid4().hex[:12]}.{extension}"

    # 1. Try Cloudinary if configured (Free Cloud Storage)
    if is_cloudinary_configured():
        try:
            url, provider = upload_file_to_cloudinary(file_storage, unique_name)
            return url, provider
        except Exception as err:
            print(f"[STORAGE WARNING] Cloudinary upload failed ({err}).")

    # 2. Try AWS S3 if configured
    if is_s3_configured():
        try:
            url, provider = upload_file_to_s3(file_storage, unique_name)
            return url, provider
        except Exception as err:
            print(f"[STORAGE WARNING] S3 upload failed ({err}). Storing locally as fallback.")

    # 3. Local disk fallback (app/static/uploads/)
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)
    local_file_path = upload_folder / unique_name
    
    file_storage.seek(0)
    file_storage.save(str(local_file_path))
    
    local_url = f"/static/uploads/{unique_name}"
    print(f"[LOCAL STORAGE] Saved '{unique_name}' locally to {local_file_path}")
    return local_url, "Local Storage (Dev Fallback)"

def test_s3_connection() -> dict:
    """Diagnostic check for AWS S3 status to demonstrate in Cloud Lab."""
    cfg = current_app.config
    if not is_s3_configured():
        return {
            "status": "Disabled",
            "message": "AWS S3 is not enabled in .env (USE_S3=false or bucket name missing). Local storage is active.",
            "bucket": cfg.get("S3_BUCKET_NAME", "N/A"),
            "region": cfg.get("AWS_REGION", "N/A")
        }

    try:
        s3 = get_s3_client()
        bucket = cfg.get("S3_BUCKET_NAME")
        s3.head_bucket(Bucket=bucket)
        return {
            "status": "Connected (Online)",
            "message": f"Successfully connected to AWS S3 bucket: '{bucket}'",
            "bucket": bucket,
            "region": cfg.get("AWS_REGION")
        }
    except Exception as e:
        return {
            "status": "Error",
            "message": f"Failed to connect to AWS S3: {str(e)}",
            "bucket": cfg.get("S3_BUCKET_NAME"),
            "region": cfg.get("AWS_REGION")
        }
