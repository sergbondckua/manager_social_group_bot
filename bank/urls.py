from django.urls import path
import bank.views

urlpatterns = [
    path(
        route="api/get_cards/<int:client_id>/",
        view=bank.views.GetCardsView.as_view(),
        name="get_cards",
    ),
]
