from django.db.models.enums import TextChoices


class PeriodicityChoices(TextChoices):
    """ Періодичність надсилання повідомлення """

    ONCE = "once", "Один раз"
    DAILY = "daily", "Щоденно"
    WEEKLY = "weekly", "Щотижнево"
    MONTHLY = "monthly", "Щомісячно"
