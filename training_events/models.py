from datetime import timedelta

from django.db import models
from django.utils import timezone

from common.models import BaseModel
from profiles.models import ClubUser


class TrainingEvent(BaseModel):
    """Модель для групових тренувань"""

    def get_upload_path(self, filename):
        """Генеруємо унікальне ім'я файлу і повертаємо шлях до нього"""
        return f"trainings/{self.created_by.id}/images/{filename}"

    title = models.CharField(
        verbose_name="Назва тренування", max_length=200, unique=True
    )
    slug = models.SlugField(
        verbose_name="name",
        unique=True,
        help_text="Назва тільки маленькими латинськими літерами",
    )
    description = models.TextField(
        verbose_name="Опис тренування", blank=True, null=True
    )
    date = models.DateTimeField(
        verbose_name="Дата та час", help_text="Дата та час тренування"
    )
    location = models.CharField(
        verbose_name="Місце", max_length=300, help_text="Місце тренування"
    )

    poster = models.ImageField(
        verbose_name="Постер тренування",
        null=True,
        blank=True,
        help_text="Постер тренування",
        upload_to=get_upload_path,
    )
    created_by = models.ForeignKey(
        verbose_name="Організатор",
        to=ClubUser,
        on_delete=models.CASCADE,
        related_name="created_trainings",
    )
    is_cancelled = models.BooleanField(verbose_name="Скасовано", default=False)
    cancellation_reason = models.TextField(
        verbose_name="Причина скасування", blank=True
    )

    def __str__(self):
        return f"{self.title} - {self.date.strftime('%d.%m.%Y %H:%M')}"

    @property
    def is_past(self):
        return self.date < timezone.now()

    @property
    def is_soon(self):
        now = timezone.now()
        return now < self.date < (now + timedelta(hours=24))

    @property
    def participant_count(self):
        return self.registrations.count()

    @property
    def has_available_slots(self):
        if self.distances.max_participants == 0:  # необмежена кількість
            return True
        return self.registrations.count() < self.distances.max_participants

    @property
    def available_distances(self):
        """Повертає список доступних дистанцій"""
        return self.distances.all().order_by("distance")

    class Meta:
        ordering = ["date"]
        verbose_name = "🏃‍♀️ Тренування"
        verbose_name_plural = "🏃‍♀️ Тренування"


class TrainingDistance(BaseModel):
    """Модель для дистанцій у тренуваннях"""

    def get_upload_path(self, filename: str) -> str:
        """Генеруємо унікальне ім'я файлу і повертаємо шлях до нього"""
        if self.training and self.training.created_by:
            return f"trainings/{self.training.created_by.id}/gpx/{filename}"
        return f"trainings/unknown-{self.id}/gpx/{filename}"

    training = models.ForeignKey(
        verbose_name="Тренування",
        to=TrainingEvent,
        on_delete=models.CASCADE,
        related_name="distances",
    )
    distance = models.FloatField(
        verbose_name="Дистанція", help_text="Дистанція в кілометрах"
    )
    pace_min = models.TimeField(
        verbose_name="Мінімальний темп",
        null=True,
        blank=True,
        help_text="Мінімальний темп (хв/км)",
    )
    pace_max = models.TimeField(
        verbose_name="Максимальний темп",
        null=True,
        blank=True,
        help_text="Максимальний темп (хв/км)",
    )
    max_participants = models.IntegerField(
        verbose_name="Максимальна кількість учасників",
        default=0,
        help_text="0 означає необмежену кількість",
    )
    route_gpx = models.FileField(
        verbose_name="Маршрут",
        upload_to=get_upload_path,
        null=True,
        blank=True,
        help_text="GPX файл маршруту",
    )

    def __str__(self):
        return f"{self.training.title} - {self.distance} км"

    class Meta:
        abstract = False
        ordering = ["distance"]
        unique_together = ("training", "distance")
        verbose_name = "️📏 Дистанція"
        verbose_name_plural = "📏 Дистанції"


class TrainingRegistration(BaseModel):
    training = models.ForeignKey(
        verbose_name="Тренування",
        to=TrainingEvent,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    distance = models.ForeignKey(
        verbose_name="Дистанція",
        to=TrainingDistance,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    participant = models.ForeignKey(
        verbose_name="Учасник",
        to=ClubUser,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    attendance_confirmed = models.BooleanField(
        verbose_name="Підтвердження участі",
        default=False,
        help_text="Підтвердження участі",
    )
    actual_attendance = models.BooleanField(
        verbose_name="Фактична відвідуваність",
        null=True,
        blank=True,
        help_text="Фактична відвідуваність",
    )
    # Додаткові дані
    expected_pace = models.IntegerField(
        verbose_name="Очікуваний темп",
        null=True,
        blank=True,
        help_text="Очікуваний темп в секундах на кілометр",
    )
    notes = models.TextField(
        blank=True, null=True, help_text="Додаткові нотатки учасника"
    )

    def __str__(self):
        return f"{self.training.title} - {self.participant.username}"

    class Meta:
        unique_together = ("training", "participant")
        verbose_name = "📝 Реєстрацію"
        verbose_name_plural = "🧑‍🤝‍🧑 Зареєстровані"
