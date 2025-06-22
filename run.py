#!/usr/bin/env python3
"""
Run script for Mossie application
"""
import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the application
from temp import app

if __name__ == "__main__":
    app.run(debug=True, port=5000)
