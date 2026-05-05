"""WSGI config for piki_ora_clinic.

Vercel imports `app` from this module to serve the application.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "piki_ora_clinic.settings")

application = get_wsgi_application()
# Vercel's @vercel/python runtime looks for a callable named `app`.
app = application
