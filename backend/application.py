# Azure App Service Entry Point
# This file serves as the entry point for Azure App Service
import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

# Azure App Service expects 'application' or 'app'
application = app
