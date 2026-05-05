#!/usr/bin/env bash
# Vercel build script - installs Python deps and gathers static assets.
# Note: NOT using `set -e` so errors print to logs rather than aborting silently.

echo "==> BUILD START"

echo "==> Python version:"
python3.12 --version 2>/dev/null || python3 --version 2>/dev/null || python --version

echo "==> Locating pip..."
PIP_CMD="python3.12 -m pip"
if ! python3.12 --version >/dev/null 2>&1; then
  PIP_CMD="python3 -m pip"
fi
echo "Using: $PIP_CMD"

echo "==> Upgrading pip..."
$PIP_CMD install --upgrade pip --break-system-packages

echo "==> Installing Python dependencies..."
$PIP_CMD install -r requirements.txt --break-system-packages

echo "==> Collecting static files..."
PY_CMD="python3.12"
if ! python3.12 --version >/dev/null 2>&1; then
  PY_CMD="python3"
fi
$PY_CMD manage.py collectstatic --noinput --clear

echo "==> Running database migrations..."
$PY_CMD manage.py migrate --noinput

echo "==> Seeding initial data (admin user, sample doctors, slots)..."
$PY_CMD manage.py seed_data || echo "Seed step had issues (this is OK if data already exists)"

echo "==> BUILD END"
