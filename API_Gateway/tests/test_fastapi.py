#!/usr/bin/env python3
"""Test script to debug FastAPI startup"""

import sys
import os
sys.path.append('src')

try:
    print("1. Testing FastAPI import...")
    import uvicorn
    from fastapi import FastAPI
    print("✅ FastAPI imports OK")

    print("2. Testing client imports...")
    from api_gateway.clients import LLMClient, EmbeddingsClient
    print("✅ Client imports OK")

    print("3. Testing FastAPI server import...")
    from api_gateway.fastapi_server import app, main
    print("✅ FastAPI server import OK")

    print("4. Starting server...")
    print("Server starting on http://localhost:8000")
    main()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()