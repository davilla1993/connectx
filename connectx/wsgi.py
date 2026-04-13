"""
WSGI config for connectx project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

os.environ['PGCLIENTENCODING'] = 'UTF8'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'connectx.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
