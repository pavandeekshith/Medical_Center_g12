import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'CS'
    
    # Database configuration
    DB_HOST = os.environ.get('DB_HOST') or '10.0.116.125'
    DB_USER = os.environ.get('DB_USER') or 'cs432g12'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'T7XnJqYz'
    DB_NAME = os.environ.get('DB_NAME') or 'cs432g12'
    CIMS_DB_NAME = os.environ.get('CIMS_DB_NAME') or 'cs432cims'
    
    # Application configuration
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
