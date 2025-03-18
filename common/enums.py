from django.db.models.enums import TextChoices


class GreetingTypeChoices(TextChoices):
    BIRTHDAY = "birthday", "День народження"
    NEW_YEAR = "new_year", "Новий рік"
