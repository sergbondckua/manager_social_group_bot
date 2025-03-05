from django.urls import path
from bank import views

urlpatterns = [
    path(
        route="api/get_cards/<int:client_id>/",
        view=views.GetCardsView.as_view(),
        name="get_cards",
    ),
    path(
        route="webhook/monobank/",
        view=views.MonobankWebhookView.as_view(),
        name="monobank_webhook",
    ),
]

app_name = "bank"