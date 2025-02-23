from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.views import View

from bank.models import MonoBankClient
from bank.services.mono import get_id_creditcard


class GetCardsView(PermissionRequiredMixin, View):
    """Отримує список карток для вибраного клієнта, доступно авторизованим користувачам із певними правами"""

    permission_required = "bank.view_monobankclient"

    def get(self, request, client_id):
        client = MonoBankClient.objects.filter(pk=client_id).first()
        if not client:
            return JsonResponse({"cards": []}, status=404)

        card_choices = get_id_creditcard(client.client_token)
        return JsonResponse(
            {"cards": [{"id": c[0], "name": c[1]} for c in card_choices]}
        )
