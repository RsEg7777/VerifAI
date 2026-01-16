"""
Vercel serverless function handler for Flask app
This file makes the Flask app compatible with Vercel's serverless environment
"""
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel expects a handler function that receives a request object
def handler(request):
    """
    Vercel serverless function handler
    Converts Vercel request to WSGI and calls Flask app
    """
    # Build WSGI environ from Vercel request
    environ = {
        'REQUEST_METHOD': request.method,
        'PATH_INFO': request.path,
        'QUERY_STRING': request.query_string or '',
        'CONTENT_TYPE': request.headers.get('Content-Type', ''),
        'CONTENT_LENGTH': str(len(request.body) if request.body else 0),
        'SERVER_NAME': request.headers.get('Host', 'localhost').split(':')[0],
        'SERVER_PORT': request.headers.get('X-Forwarded-Port', '443' if request.headers.get('X-Forwarded-Proto') == 'https' else '80'),
        'wsgi.version': (1, 0),
        'wsgi.url_scheme': request.headers.get('X-Forwarded-Proto', 'https'),
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
    }
    
    # Add HTTP headers
    for key, value in request.headers.items():
        key_upper = key.upper().replace('-', '_')
        if key_upper not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            environ[f'HTTP_{key_upper}'] = value
    
    # Handle request body
    import io
    if request.body:
        environ['wsgi.input'] = io.BytesIO(request.body)
    else:
        environ['wsgi.input'] = io.BytesIO()
    
    # Response data
    response_data = {'status': 200, 'headers': {}, 'body': []}
    
    def start_response(status, response_headers):
        response_data['status'] = int(status.split()[0])
        response_data['headers'] = dict(response_headers)
    
    # Call Flask app
    response_iter = app(environ, start_response)
    
    # Collect response body
    try:
        body_parts = []
        for part in response_iter:
            if isinstance(part, bytes):
                body_parts.append(part)
            else:
                body_parts.append(str(part).encode('utf-8'))
        response_body = b''.join(body_parts)
    finally:
        if hasattr(response_iter, 'close'):
            response_iter.close()
    
    # Return Vercel response format
    # Vercel Python runtime expects a Response object or dict
    try:
        from vercel import Response
        vercel_response = Response()
        vercel_response.status = response_data['status']
        vercel_response.headers = response_data['headers']
        if isinstance(response_body, bytes):
            vercel_response.body = response_body.decode('utf-8')
        else:
            vercel_response.body = str(response_body)
        return vercel_response
    except ImportError:
        # Fallback if vercel package is not available
        # Return dict format (some Vercel runtimes accept this)
        return {
            'statusCode': response_data['status'],
            'headers': response_data['headers'],
            'body': response_body.decode('utf-8') if isinstance(response_body, bytes) else str(response_body)
        }
