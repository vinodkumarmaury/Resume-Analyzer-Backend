#!/usr/bin/env bash
# build.sh

set -o errexit  # exit on error

# Upgrade pip first
pip install --upgrade pip

# Install packages with specific strategies for problematic ones
pip install --upgrade setuptools wheel

# Install requirements
pip install -r requirements.txt

# Try to install spaCy model (optional - won't fail build if it fails)
python -m spacy download en_core_web_sm || echo "Warning: Could not download spaCy model, continuing..."

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
