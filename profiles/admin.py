from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from profiles.models import ClubUser


@admin.register(ClubUser)
class ProfileAdmin(UserAdmin):
    """
    Адміністративна панель для управління моделлю ClubUser.
    """

    # Відображення повного імені користувача
    @admin.display(description=_("Full Name"))
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    # Список відображуваних полів у таблиці
    list_display = (
        "username",
        "full_name",
        "telegram_id",
        "phone_number",
        "is_staff",
        "is_active",
    )
    list_display_links = ("username", "full_name")  # Поля, що є посиланнями
    list_editable = ("is_active",)  # Поля, які можна редагувати прямо у списку
    readonly_fields = (
        "telegram_username",
        "telegram_first_name",
        "telegram_last_name",
        "telegram_photo_id",
        "telegram_language_code",
        "last_login",
        "date_joined",
    )  # Поля, які не можна редагувати
    search_fields = (
        "username",
        "email",
        "phone_number",
        "telegram_id",
    )  # Поля для пошуку
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
    )  # Фільтри для списку

    # Групування полів у формі редагування
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Персональні дані",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "data_of_birth",
                    "phone_number",
                    "email",
                )
            },
        ),
        (
            "Телеграм інформація",
            {
                "fields": (
                    "telegram_id",
                    "telegram_username",
                    "telegram_first_name",
                    "telegram_last_name",
                    "telegram_photo_id",
                    "telegram_language_code",
                ),
            },
        ),
        (
            "Права доступу",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Дата", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "telegram_id",
                    "data_of_birth",
                    "phone_number",
                ),
            },
        ),
    ) + UserAdmin.add_fieldsets
