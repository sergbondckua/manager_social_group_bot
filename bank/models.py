from django.db import models
from common.models import BaseModel


class MonoBankClient(BaseModel):
    """Клієнт Монобанку"""

    name = models.CharField(max_length=100, verbose_name="Назва")
    client_token = models.CharField(
        max_length=100, verbose_name="Токен клієнта"
    )

    def __str__(self):
        return self.name


class MonoBankCard(BaseModel):
    """Картки клієнта Монобанку"""

    client = models.ForeignKey(
        MonoBankClient,
        on_delete=models.CASCADE,
        verbose_name="Клієнт",
        related_name="cards",
    )
    card_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="ID картки",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активний")

    def __str__(self):
        return f"{self.client.name} - {self.card_id or 'Без ID'}"
