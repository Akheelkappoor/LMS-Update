import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

class Config:
    """Base configuration class"""
    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-this-in-production'
    
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'lms.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    
    # Email configuration (you'll need to update these)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Application configuration
    POSTS_PER_PAGE = 20
    LANGUAGES = ['en', 'hi']  # English and Hindi support
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(Config.basedir, 'instance'), exist_ok=True)
        os.makedirs(os.path.join(Config.basedir, 'data'), exist_ok=True)
        
        # Log email configuration
        app.logger.debug(f"MAIL_SERVER: {app.config['MAIL_SERVER']}")
        app.logger.debug(f"MAIL_PORT: {app.config['MAIL_PORT']}")
        app.logger.debug(f"MAIL_USE_TLS: {app.config['MAIL_USE_TLS']}")
        app.logger.debug(f"MAIL_USERNAME: {app.config['MAIL_USERNAME']}")
        app.logger.debug(f"MAIL_DEFAULT_SENDER: {app.config['MAIL_DEFAULT_SENDER']}")