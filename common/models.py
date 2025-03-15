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


class Compliment(BaseModel):
    """ Модель для збереження комплементів """

    text = models.TextField(
        verbose_name="Текст компліменту"
    )

    def __str__(self):
        return f"{self.id}: {self.text[3:50]}"

    class Meta:
        verbose_name = "Комплімент"
        verbose_name_plural = "Компліменти"
