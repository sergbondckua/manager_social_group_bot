from django import forms
from .models import MonoBankCard, MonoBankClient
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


class MonobankStatementForm(forms.Form):
    """Форма для отримання виписки з API Монобанку."""

    client_token = forms.ModelChoiceField(
        queryset=MonoBankClient.objects.all(),
        label="Клієнт",
        help_text="Оберіть клієнта для взаємодії з API Монобанку",
        widget=forms.Select(attrs={"onchange": "updateCards(this)"}),
    )
    card_id = forms.ChoiceField(
        choices=[],  # Порожній список для ініціалізації
        label="ID картки",
        help_text="Оберіть картку для отримання виписки",
        widget=forms.Select(),
    )
    date_from = forms.DateField(
        label="Дата початку",
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Оберіть початкову дату виписки",
    )
    date_to = forms.DateField(
        label="Дата завершення",
        widget=forms.DateInput(attrs={"type": "date"}),
        help_text="Оберіть кінцеву дату виписки",
    )

    def __init__(self, *args, **kwargs):
        client_id = kwargs.pop("client_id", None)  # Отримуємо client_id
        super().__init__(*args, **kwargs)
        if client_id:
            cards = MonoBankCard.objects.filter(
                client_id=client_id, is_active=True
            )
            card_choices = [(card.card_id, card.card_id) for card in cards]
            print(card_choices, flush=True)
            self.fields["card_id"].choices = card_choices
