"""
Vercel Serverless Function Entry Point for FastAPI Backend
"""
import sys
import os

# Add parent directory to path so we can import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.api.main import create_app

# Create the FastAPI app
app = create_app()

# For Vercel, we need to expose the ASGI app using Mangum
from mangum import Mangum
handler = Mangum(app)

if __name__ == "__main__":
    # For local testing only
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
