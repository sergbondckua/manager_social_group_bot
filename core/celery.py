import os

from celery import Celery
from celery.schedules import crontab

# Встановіть стандартний модуль налаштувань Django.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Завантажувати модулі завдань з усіх зареєстрованих програм Django.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


# Запланування повідомлень
# app.conf.beat_schedule = {
#     'send-scheduled-messages': {
#         'task': 'chronopost.tasks.send_scheduled_messages',
#         'schedule': crontab(minute='*/1'),  # Перевіряти кожну хвилину
#     },
# }