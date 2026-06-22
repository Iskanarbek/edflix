#!/bin/bash
set -e

echo "Installing dependencies..."
pip3 install --break-system-packages -r requirements.txt

echo "Collecting static files..."
python3 manage.py collectstatic --noinput

echo "Copying to staticfiles_build..."
mkdir -p staticfiles_build/static
cp -r staticfiles/. staticfiles_build/static/

echo "Build complete."
