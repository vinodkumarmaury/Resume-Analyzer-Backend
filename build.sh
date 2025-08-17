#!/usr/bin/env bash
# build.sh

set -o errexit  # exit on error

pip install --upgrade pip
pip install -r requirements.txt

# Install spaCy model (required for resume analysis)
python -m spacy download en_core_web_sm

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate
