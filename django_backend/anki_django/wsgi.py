"""WSGI config for cPanel/Passenger deployment."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "anki_django.settings")

application = get_wsgi_application()
