"""
ASGI config for recommenderx project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Use production settings if RAILWAY_ENVIRONMENT is set
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recommenderx.settings")

application = get_asgi_application()
