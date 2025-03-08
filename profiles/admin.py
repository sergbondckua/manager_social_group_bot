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
        "is_active",
    )
    list_display_links = ("username", "full_name")  # Поля, що є посиланнями
    list_editable = ("is_active",)  # Поля, які можна редагувати прямо у списку
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
            _("Personal Info"),
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
            _("Telegram Info"),
            {
                "fields": ("telegram_id",),
            },
        ),
        (
            _("Permissions"),
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
        (_("Important Dates"), {"fields": ("last_login", "date_joined")}),
    )

    # Покращення сортування та фільтрації, якщо необхідно
    ordering = ("username",)  # Сортування за замовчуванням
    readonly_fields = ("last_login", "date_joined")  # Поля тільки для читання
