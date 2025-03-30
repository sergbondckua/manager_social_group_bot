from django.urls import path

from robot.views import WebhookView

urlpatterns = [
    path("webhook/", WebhookView.as_view(), name="telegram-webhook"),
]

app_name = "robot"