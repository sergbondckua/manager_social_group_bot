from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe
from profiles.models import ClubUser


@admin.register(ClubUser)
class ProfileAdmin(UserAdmin):
    """
    Адміністративна панель для управління моделлю ClubUser.
    """

    # Відображення повного імені користувача
    @admin.display(description=mark_safe("ПІБ"))
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    list_display = (
        "full_name",
        "username",
        "telegram_id",
        "phone_number",
        "data_of_birth",
        "get_tg_photo",
        "is_active",
    )
    list_display_links = ("username", "full_name")
    list_editable = ("is_active",)
    ordering = ("-date_joined",)
    readonly_fields = (
        "telegram_username",
        "telegram_first_name",
        "telegram_last_name",
        "telegram_photo",
        "get_tg_photo",
        "telegram_language_code",
        "last_login",
        "date_joined",
    )
    search_fields = (
        "username",
        "email",
        "phone_number",
        "telegram_id",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
    )

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
                    "get_tg_photo",
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

    def get_tg_photo(self, obj):
        """Мініатюра зображення"""
        if photo := obj.telegram_photo:
            return mark_safe(
                f'<a href="{photo.url}" target="_blank">'
                f'<img src="{photo.url}" height="40" width="auto" alt="Photo" /></a>'
            )
        return "-"

    get_tg_photo.short_description = "Фото"
