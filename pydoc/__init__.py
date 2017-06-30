# Load Celery before tasks get a chance to load
from pydoc.celery import app
