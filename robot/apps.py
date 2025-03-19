from django.apps import AppConfig


class RobotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "robot"
    verbose_name = "Бот"

    # def ready(self):
    #     # Імпортуємо сигнали
    #     from robot import signals
