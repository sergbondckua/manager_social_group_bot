from django import forms
from .models import MonoBankCard
from bank.services.mono import get_id_creditcard


class MonoBankCardAdminForm(forms.ModelForm):
    class Meta:
        model = MonoBankCard
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Якщо ми редагуємо об'єкт і є клієнт, додаємо choices
        if self.instance.pk and self.instance.client:
            client = self.instance.client
            card_choices = get_id_creditcard(client.client_token)
            self.fields["card_id"].widget = forms.Select(choices=card_choices)
        else:
            # Якщо об'єкт новий, поле card_id залишиться порожнім
            self.fields["card_id"].widget = forms.Select(choices=[])
