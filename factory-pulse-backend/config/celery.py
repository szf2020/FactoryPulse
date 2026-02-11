import os
from celery import Celery

# Set the default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Read Django settings with the 'CELERY_' namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks in installed apps (e.g., core.tasks)
app.autodiscover_tasks()