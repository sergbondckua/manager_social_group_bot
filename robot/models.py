import uuid

from django.db import models

from common.models import BaseModel


class QuizQuestion(BaseModel):
    """Модель запитань для квізу"""

    def get_upload_path(self, filename):
        # Генерируем уникальное имя файла и возвращаем путь к нему

        file_extension = filename.split(".")[-1]
        new_filename = f"{uuid.uuid4().hex}.{file_extension}"
        return f"quiz/images/{self.id}/{new_filename}"

    text = models.CharField(verbose_name="Запитання", max_length=255)
    explanation = models.TextField(
        verbose_name="Пояснення", blank=True, null=True, max_length=200
    )
    image = models.ImageField(
        verbose_name="Зображення",
        blank=True,
        null=True,
        upload_to=get_upload_path,
    )
    is_active = models.BooleanField(verbose_name="Активне", default=True)

    def __str__(self):
        return f"ID: {self.id} - {self.text[:20]}..."

    class Meta:
        verbose_name = "🤔️ Quiz-Запитання"
        verbose_name_plural = "🤔 Quiz-Запитання"


class QuizAnswer(BaseModel):
    """Модель відповіді на запитання квізу"""

    question = models.ForeignKey(
        to=QuizQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Запитання",
    )
    text = models.CharField(verbose_name="Відповідь", max_length=50)
    is_correct = models.BooleanField(verbose_name="Вірна", default=False)

    def __str__(self):
        return f"ID: {self.id} - {self.question.text[:20]}..."

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('question',),
                condition=models.Q(is_correct=True),
                name='unique_correct_answer'
            )
        ]
        verbose_name = "Відповідь на запитання квізу"
        verbose_name_plural = "Відповіді на запитання квізу"
