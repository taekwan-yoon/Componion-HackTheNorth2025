#!/usr/bin/env python3
"""
Development server runner for HTN 2025 Backend
"""

import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    print("Starting HTN 2025 Backend Development Server...")
    print(f"Server will be available at: http://localhost:{app.config.get('PORT', 5000)}")
    print("Press Ctrl+C to stop the server")
    
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=True
    )
