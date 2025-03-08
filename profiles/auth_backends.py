from django.contrib.auth.backends import BaseBackend
from profiles.models import ClubUser


class TelegramOrUsernameAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, telegram_id=None, **kwargs):
        try:
            if telegram_id:
                return ClubUser.objects.get(telegram_id=telegram_id)
            elif username:
                return ClubUser.objects.get(username=username)
        except ClubUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return ClubUser.objects.get(pk=user_id)
        except ClubUser.DoesNotExist:
            return None
