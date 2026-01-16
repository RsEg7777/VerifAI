"""
Vercel serverless function handler for Flask app
This file makes the Flask app compatible with Vercel's serverless environment
"""
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment for serverless (if not already set)
if not os.environ.get('DATABASE_URL'):
    # Use in-memory SQLite for serverless (ephemeral)
    # For production, set DATABASE_URL to a PostgreSQL connection string
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

try:
    # Import Flask app
    from app import app
    
    # Vercel's @vercel/python builder automatically handles WSGI apps
    # Export the app - Vercel will handle WSGI conversion
    handler = app
    
except Exception as e:
    # If there's an import error, create a minimal error handler
    from flask import Flask
    error_app = Flask(__name__)
    
    @error_app.route('/', defaults={'path': ''})
    @error_app.route('/<path:path>')
    def error_handler(path):
        return {
            'error': 'Application initialization failed',
            'message': str(e),
            'type': type(e).__name__
        }, 500
    
    handler = error_app
