"""Celery application instantiation"""

import os

from celery import Celery
from django.conf import settings


def create_application():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pydoc.settings.local')
    app = Celery('pydoc')
    app.config_from_object('django.conf:settings')
    app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
    return app


app = create_application()
