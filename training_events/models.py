import logging
import uuid
from datetime import timedelta

from django.core.validators import (
    FileExtensionValidator,
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models, transaction
from django.utils import timezone
from django.utils.timezone import localtime

from common.models import BaseModel
from profiles.models import ClubUser
from training_events.enums import TrainingMapProcessingStatusChoices

logger = logging.getLogger(__name__)


class TrainingEvent(BaseModel):
    """Модель для групових тренувань"""

    def get_upload_path(self, filename):
        """Генеруємо унікальне ім'я файлу і повертаємо шлях до нього"""
        file_extension = filename.split(".")[-1]
        new_filename = f"{uuid.uuid4().hex}.{file_extension}"
        return f"trainings/{self.created_by.id}/images/{new_filename}"

    title = models.CharField(
        verbose_name="Назва тренування", max_length=100, unique=True
    )
    description = models.TextField(
        verbose_name="Опис тренування", blank=True, null=True
    )
    date = models.DateTimeField(
        verbose_name="Дата та час", help_text="Дата та час тренування"
    )
    location = models.CharField(
        verbose_name="Місце", max_length=150, help_text="Місце тренування"
    )

    poster = models.ImageField(
        verbose_name="Постер тренування",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "svg", "webp"]
            )
        ],
        upload_to=get_upload_path,
    )
    created_by = models.ForeignKey(
        verbose_name="Організатор",
        to=ClubUser,
        on_delete=models.CASCADE,
        related_name="created_trainings",
    )
    is_cancelled = models.BooleanField(verbose_name="Скасовано", default=False)
    is_feedback_sent = models.BooleanField(
        default=False,
        verbose_name="Оцінювання надіслано",
        help_text="Чи було відправлено запит на оцінювання тренування.",
    )
    cancellation_reason = models.TextField(
        verbose_name="Причина скасування", blank=True
    )

    def __str__(self):
        local_date = localtime(
            self.date
        )  # Конвертуємо дату в локальну часову зону
        distances = ", ".join(
            [f"{d.distance} км" for d in self.available_distances]
        )
        return (
            f"{self.title} - {local_date.strftime('%d %B %Y %H:%M')}: "
            f"{self.location}, {distances}"
        )

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
        verbose_name = "👟️ Тренування"
        verbose_name_plural = "👟 Тренування"


class TrainingDistance(BaseModel):
    """Модель для дистанцій у тренуваннях"""

    def get_upload_path(self, filename: str) -> str:
        """Генеруємо унікальне ім'я файлу і повертаємо шлях до нього"""

        if self.training and self.training.created_by:
            file_extension = filename.split(".")[-1]
            new_filename = (
                f"{self.distance}km_"
                f"{self.training_id}_"
                f"{self.training.date.strftime('%d%B%Y')}.{file_extension}"
            )
            return (
                f"trainings/{self.training.created_by.id}/gpx/{new_filename}"
            )
        return f"trainings/unknown/gpx/{filename}"

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
        validators=[FileExtensionValidator(allowed_extensions=["gpx"])],
        null=True,
        blank=True,
        help_text="GPX файл маршруту: .gpx",
    )
    route_gpx_map = models.ImageField(
        verbose_name="Карта маршруту",
        upload_to=get_upload_path,
        max_length=255,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "svg", "webp"]
            )
        ],
        null=True,
        blank=True,
        help_text="Карта маршруту: .jpg, .jpeg, .png, .svg, .webp",
    )
    # Поле для відстеження статусу обробки
    map_processing_status = models.CharField(
        verbose_name="Статус обробки карти",
        max_length=20,
        choices=TrainingMapProcessingStatusChoices.choices,
        default=TrainingMapProcessingStatusChoices.PENDING,
        blank=True,
    )

    def save(self, *args, **kwargs):
        """Перевизначений метод збереження для асинхронного створення візуалізації маршруту"""

        # Перевіряємо чи це новий об'єкт з GPX файлом
        is_new_gpx = False
        if self.pk:
            # Якщо об'єкт вже існує, перевіряємо чи змінився GPX файл
            try:
                old_instance = TrainingDistance.objects.get(pk=self.pk)
                is_new_gpx = self.route_gpx and (
                    not old_instance.route_gpx
                    or self.route_gpx.name != old_instance.route_gpx.name
                )
            except TrainingDistance.DoesNotExist:
                is_new_gpx = bool(self.route_gpx)
        else:
            # Новий об'єкт
            is_new_gpx = bool(self.route_gpx)

        # Зберігаємо об'єкт
        super().save(*args, **kwargs)

        # Якщо є новий GPX файл і немає карти, запускаємо асинхронну обробку
        if is_new_gpx and not self.route_gpx_map:
            self.map_processing_status = (
                TrainingMapProcessingStatusChoices.PENDING
            )
            super().save()

            # Запускаємо асинхронну задачу після завершення транзакції
            transaction.on_commit(lambda: self._create_visualization_async())

    def _create_visualization_async(self):
        """Запускає асинхронну задачу для створення візуалізації"""
        try:
            from robot.tasks import create_route_visualization_task
            create_route_visualization_task.delay(self.pk)
        except Exception as e:
            logger.error(
                "Помилка при запуску асинхронної задачі для дистанції %s: %s",
                self.pk,
                e,
            )
            # Встановлюємо статус помилки
            TrainingDistance.objects.filter(pk=self.pk).update(
                map_processing_status=TrainingMapProcessingStatusChoices.FAILED
            )

    def __str__(self):
        name = "".join(
            s[0].upper() for s in self.training.title.split(" ") if s.isalpha()
        )
        return f"{self.distance} км - {name}_{self.training.id}"

    class Meta:
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


class TrainingRating(BaseModel):
    training = models.ForeignKey(
        verbose_name="Тренування",
        to=TrainingEvent,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    participant = models.ForeignKey(
        verbose_name="Учасник",
        to=ClubUser,
        on_delete=models.CASCADE,
        related_name="ratings",
    )
    rating = models.IntegerField(
        verbose_name="Рейтинг",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Рейтинг учасника від 1 до 10",
    )

    def __str__(self):
        return (
            f"{self.training.title} - "
            f"{self.participant.get_full_name() or self.participant.username}: "
            f"{self.rating}/5"
        )

    class Meta:
        unique_together = ("training", "participant")
        verbose_name = "🌟 Рейтинг"
        verbose_name_plural = "🌟 Рейтинги"


class TrainingComment(BaseModel):
    training = models.ForeignKey(
        verbose_name="Тренування",
        to=TrainingEvent,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    participant = models.ForeignKey(
        verbose_name="Учасник",
        to=ClubUser,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    comment = models.TextField(
        verbose_name="Коментар",
        help_text="Коментар учасника",
    )
    is_public = models.BooleanField(
        default=True, help_text="Чи видимий коментар іншим учасникам"
    )

    def __str__(self):
        return (
            f"{self.training.title} - "
            f"{self.participant.get_full_name() or self.participant.username}"
        )

    class Meta:
        verbose_name = "💬 Відгук"
        verbose_name_plural = "💬 Відгуки"
        ordering = ["-created_at"]
