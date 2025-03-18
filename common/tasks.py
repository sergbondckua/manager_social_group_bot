from celery import shared_task
from django.utils import timezone

from profiles.models import ClubUser


@shared_task
async def send_birthday_greetings():
    today = timezone.now().date()
    users = ClubUser.objects.filter(
        data_of_birth__day=today.day,
        data_of_birth__month=today.month,
        is_active=True,
    )
