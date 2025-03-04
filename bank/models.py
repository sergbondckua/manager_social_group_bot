from django.db import models
from common.models import BaseModel


class MonoBankClient(BaseModel):
    """Клієнт Монобанку"""

    name = models.CharField(
        max_length=100,
        verbose_name="Назва клієнта",
        help_text="Назва клієнта, ідентифікація, призначення",
    )
    client_token = models.CharField(
        max_length=100,
        verbose_name="Токен клієнта",
        help_text="Токен клієнта, для взаємодії з API Монобанку",
    )
    is_active = models.BooleanField(verbose_name="Діє", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "🏦 Клієнт (monobank)"
        verbose_name_plural = "🏦 Клієнти (monobank)"


class MonoBankCard(BaseModel):
    """Картки клієнта Монобанку"""

    client = models.ForeignKey(
        MonoBankClient,
        on_delete=models.CASCADE,
        verbose_name="Клієнт",
        related_name="cards",
        help_text="Клієнт, якому належать картки",
    )
    card_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="ID картки",
        help_text="ID картки, для взаємодії з API Монобанку",
    )
    chat_id = models.BigIntegerField(
        verbose_name="ID чату",
        blank=True,
        null=True,
        help_text="ID чату, до якого будуть відправлятися повідомлення при транзакціях по картці",
    )
    is_active = models.BooleanField(default=True, verbose_name="Дієва")

    def __str__(self):
        return f"{self.client.name} - {self.card_id or 'Без ID'}"

    class Meta:
        verbose_name = "💳 Картка (monobank)"
        verbose_name_plural = "💳 Картки (monobank)"
