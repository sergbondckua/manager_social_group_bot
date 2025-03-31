from django.urls import path

from robot import views

urlpatterns = [
    path(
        "webhook/", view=views.WebhookView.as_view(), name="telegram-webhook"
    ),
]

app_name = "robot"
