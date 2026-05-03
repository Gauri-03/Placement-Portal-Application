"""
workers.py — Celery application instance with Flask context integration and Beat schedule.

Run worker:
    cd backend && uv run celery -A src.workers.workers worker --loglevel=info

Run Beat scheduler:
    cd backend && uv run celery -A src.workers.workers beat --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab
from src.app import create_app

flask_app = create_app()

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config["CELERY_BROKER_URL"],
        backend=app.config["CELERY_RESULT_BACKEND"],
    )

    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        timezone=app.config.get("CELERY_TIMEZONE", "UTC"),
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery



celery = make_celery(flask_app)


celery.conf.beat_schedule = {
    "send-daily-reminders": {
        "task": "src.workers.task.send_daily_reminders",
        "schedule": crontab(hour=8, minute=0),
    },
    "send-monthly-report": {
        "task": "src.workers.task.send_monthly_report",
        "schedule": crontab(day_of_month=1, hour=8, minute=0),
    },
}

celery.conf.timezone = "UTC"

import src.workers.task  # noqa: F401, E402
