import os
import sys

# Add the project root directory to the Python path
# This is critical for Vercel serverless — api/index.py runs in /var/task/api/
# but app.py and utils.py live one level up at /var/task/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app instance from app.py
# Vercel's @vercel/python runtime looks for an `app` variable at module level
from app import app
