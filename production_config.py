import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

class ProductionConfig:
    """Production configuration for AWS Amplify"""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-production-secret-key'
    
    # Database - PostgreSQL for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://lms_user:SecurePass123@lms-db.cluster-xyz.us-east-1.rds.amazonaws.com:5432/lms_production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = True  # HTTPS only
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File upload configuration
    UPLOAD_FOLDER = '/tmp/uploads'  # Use /tmp for serverless
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Application settings
    DEBUG = False
    TESTING = False
    
    @staticmethod
    def init_app(app):
        # Create upload directory
        os.makedirs('/tmp/uploads', exist_ok=True)