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

    text = models.CharField(
        verbose_name="Запитання",
        max_length=300,
        help_text="Максимум 300 символів",
    )
    explanation = models.TextField(
        verbose_name="Пояснення",
        blank=True,
        null=True,
        max_length=200,
        help_text="Пояснення щодо відповіді. Максимум 200 символів",
    )
    image = models.ImageField(
        verbose_name="Зображення",
        blank=True,
        null=True,
        upload_to=get_upload_path,
    )
    is_active = models.BooleanField(verbose_name="Активне", default=True)

    def __str__(self):
        return f"ID: {self.id} - {self.text[:50]}..."

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

    def save(self, *args, **kwargs):
        if self.is_correct:  # Якщо ця відповідь позначена як правильна
            # Знаходимо всі інші правильні відповіді для цього питання
            other_correct_answers = QuizAnswer.objects.filter(
                question=self.question, is_correct=True
            ).exclude(id=self.id)

            # Встановлюємо їм is_correct=False
            other_correct_answers.update(is_correct=False)

        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("question",),
                condition=models.Q(is_correct=True),
                name="unique_correct_answer",
            )
        ]
        verbose_name = "Відповідь на запитання квізу"
        verbose_name_plural = "Відповіді на запитання квізу"
