import os


class Config:
    """Application configuration.

    All sensitive values are loaded from environment variables so that
    nothing secret is hardcoded in the repository.
    """

    # Flask-Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # Google Custom Search
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    GOOGLE_CSE_ID = os.environ.get('GOOGLE_CSE_ID')

    # Sightengine API (image detection)
    SIGHTENGINE_API_USER = os.environ.get('SIGHTENGINE_API_USER')
    SIGHTENGINE_API_SECRET = os.environ.get('SIGHTENGINE_API_SECRET')

    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

    # Database configuration
    # For Vercel/serverless: Use in-memory SQLite or PostgreSQL
    # SQLite files don't persist on serverless functions
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///newsguard.db')
    
    # If on Vercel and no DATABASE_URL is set, use in-memory SQLite
    if os.environ.get('VERCEL') and not os.environ.get('DATABASE_URL'):
        database_url = 'sqlite:///:memory:'
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

