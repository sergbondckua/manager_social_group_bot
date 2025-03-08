from django.urls import path
from .views import MonobankStatementView

urlpatterns = [
    path(
        route="monobank-statement/",
        view=MonobankStatementView.as_view(),
        name="monobank_statement",
    ),
]

app_name = "bank_admin"