"""ASGI config for piki_ora_clinic."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "piki_ora_clinic.settings")

application = get_asgi_application()
