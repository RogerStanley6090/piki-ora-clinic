#!/usr/bin/env bash
# Vercel build script — installs Python deps and gathers static assets.
set -euo pipefail

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "==> Build complete."
