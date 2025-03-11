from django.urls import path
from bank import views

urlpatterns = [
    path(
        route="api/get-api-cards/<int:client_id>/",
        view=views.GetApiCardsView.as_view(),
        name="get_api_cards",
    ),
    path(
        route="api/get-cards/<int:client_id>/",
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
