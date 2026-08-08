#!/usr/bin/env python3
"""
Python backend server for Argus OSINT tool.
This script can be run as a standalone server or as a Tauri sidecar.
"""

import sys
import os

# Add the src_python directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from interfaces import api

def main():
    """Run the FastAPI server."""
    print("Starting Argus OSINT Python backend server...")
    print("API will be available at http://localhost:8000")
    
    uvicorn.run(
        api.app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )

if __name__ == "__main__":
    main()