from django.db.models.enums import TextChoices

class TrainingMapProcessingStatusChoices(TextChoices):
    """ Статус обробки карти тренувальної події """

    PENDING = "pending", "В очікуванні"
    PROCESSING = "processing", "В обробці"
    COMPLETED = "completed", "Оброблена"
    FAILED = "failed", "Помилка"