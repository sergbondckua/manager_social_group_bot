from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.validators import RegexValidator
from django.db import models


class ClubUser(AbstractUser):
    """Внесення додаткових полів в модель користувача"""

    telegram_id = models.BigIntegerField(
        verbose_name="Telegram ID",
        null=True,
        blank=True,
        unique=True,
        help_text="Унікальний ID користувача в Telegram",
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
    def __str__(self):
        return (
            f"{self.first_name} {self.last_name}: ({self.username})"
            if self.first_name and self.last_name is not None
            else self.username
        )

    class Meta:
        ordering = ("username",)
        verbose_name = "Користувача"
        verbose_name_plural = "Користувачі"
