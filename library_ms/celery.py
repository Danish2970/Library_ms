import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_ms.settings')

app = Celery('library_ms')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Scheduled tasks
app.conf.beat_schedule = {
    'due-date-reminders-daily': {
        'task': 'apps.notifications.tasks.send_due_date_reminders',
        'schedule': crontab(hour=9, minute=0),
    },
    'overdue-check-daily': {
        'task': 'apps.notifications.tasks.flag_overdue_books',
        'schedule': crontab(hour=8, minute=0),
    },
    'retrain-recommendations-nightly': {
        'task': 'apps.recommendations.tasks.retrain_recommendation_model',
        'schedule': crontab(hour=2, minute=0),
    },
}