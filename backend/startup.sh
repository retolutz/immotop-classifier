#!/bin/bash
# Azure App Service Startup Script

# Install dependencies
pip install -r requirements.txt

# Start the application with gunicorn
gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout=120 app.main:app -k uvicorn.workers.UvicornWorker
