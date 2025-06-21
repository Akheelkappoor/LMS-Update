#!/bin/bash

# Activate your virtual environment
source .venv/bin/activate

# Install new package
# pip3 install -r requirements.txt

# Start Gunicorn to run your Django application
gunicorn -c gunicorn_config.py main:app
