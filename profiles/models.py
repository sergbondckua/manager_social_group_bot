from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser


class TelegramProfileMixin(models.Model):
    """Міксін для зберігання Telegram-даних"""

    telegram_id = models.BigIntegerField(
        verbose_name="Telegram ID",
        unique=True,
        help_text="Унікальний ID користувача в Telegram",
    )
    telegram_username = models.CharField(
        verbose_name="Ім'я користувача в Telegram",
        max_length=100,
        null=True,
        blank=True,
        help_text="Ім'я користувача в Telegram",
    )
    telegram_first_name = models.CharField(
        verbose_name="Ім'я в Telegram",
        max_length=100,
        null=True,
        blank=True,
        help_text="Ім'я користувача в Telegram",
    )
    telegram_last_name = models.CharField(
        verbose_name="Прізвище в Telegram",
        max_length=100,
        null=True,
        blank=True,
        help_text="Прізвище користувача в Telegram",
    )
    telegram_photo_id = models.CharField(
        verbose_name="Фото ID в Telegram",
        max_length=150,
        null=True,
        blank=True,
        help_text="Фото користувача в Telegram",
    )
    telegram_language_code = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Мова користувача в Telegram (наприклад, 'en', 'uk')",
    )

    class Meta:
        abstract = True  # Робимо модель абстрактною


class ClubUser(AbstractUser, TelegramProfileMixin):
    """Модель користувача з Telegram-даними"""

    username = models.CharField(
        verbose_name="Ім'я користувача",
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Ім'я користувача",
    )
    data_of_birth = models.DateField(
        verbose_name="Дата народження",
        null=True,
        blank=True,
        help_text="Дата народження користувача",
    )
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,13}$",
        message="Номер телефону у форматі: '+380999999'. Допущені до 13 цифр.",
    )
    phone_number = models.CharField(
        verbose_name="Номер телефону",
        max_length=13,
        null=True,
        blank=True,
        validators=[phone_regex],
        help_text="Номер телефону користувача",
    )

    USERNAME_FIELD = (
        "telegram_id"  # Використовуємо для авторизації
    )
    REQUIRED_FIELDS = (
        ["username"]
    )  # Використовуємо telegram_id для авторизації

    def __str__(self):
        return (
            f"{self.first_name} {self.last_name} ({self.username})"
            if self.first_name or self.last_name
            else self.username
        ).strip()

    class Meta:
        ordering = ("date_joined",)
        verbose_name = "Користувача"
        verbose_name_plural = "Користувачі"
