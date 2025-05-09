"""
WSGI config for recommenderx project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Use production settings if RAILWAY_ENVIRONMENT is set
if os.getenv('RAILWAY_ENVIRONMENT'):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recommenderx.settings_production")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "recommenderx.settings")

application = get_wsgi_application()
