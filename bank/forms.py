from django import forms
from .models import MonoBankCard
from bank.services.mono import MonobankService
import logging

logger = logging.getLogger(__name__)


class MonoBankCardAdminForm(forms.ModelForm):
    class Meta:
        model = MonoBankCard
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Якщо об'єкт існує і клієнт визначений, додаємо choices
        if self.instance.pk and self.instance.client:
            client = self.instance.client
            client_token = getattr(client, "client_token", None)

            if client_token:
                try:
                    # Отримуємо список карток клієнта
                    card_choices = MonobankService(
                        client_token
                    ).get_credit_card_ids()
                    self.fields["card_id"].widget = forms.Select(
                        choices=card_choices
                    )
                except Exception as e:
                    logger.error(
                        "Не вдалося отримати список карток Monobank для клієнта %s: %s",
                        client,
                        e,
                    )
                    # У разі помилки залишаємо поле пустим
                    self.fields["card_id"].widget = forms.Select(choices=[])
            else:
                logger.warning("Клієнт не має токена Monobank.")
                self.fields["card_id"].widget = forms.Select(choices=[])
        else:
            # Якщо об'єкт новий або клієнт не визначений
            self.fields["card_id"].widget = forms.Select(choices=[])
