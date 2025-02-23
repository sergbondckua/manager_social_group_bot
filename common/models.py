from django.db import models


class BaseModel(models.Model):
    """Основна модель-робоча частина"""

    created_at = models.DateTimeField(
        verbose_name="Створено",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name="Змінено",
        auto_now=True,
    )

    class Meta:
        abstract = True
