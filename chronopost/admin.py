from django.contrib import admin
from django.utils.safestring import mark_safe

from chronopost.models import ScheduledMessage, WeatherNotification
from common.admin import BaseAdmin


@admin.register(ScheduledMessage)
class ScheduledMessageAdmin(BaseAdmin):
    """Адмін-панель для моделі ScheduledMessage."""

    save_on_top = True
    save_as = True
    readonly_fields = ("get_image",) + BaseAdmin.readonly_fields
    list_display = (
        "title",
        "chat_id",
        "scheduled_time",
        "periodicity",
        "is_active",
    )
    actions = ["make_active", "make_inactive"]
    ordering = ("scheduled_time",)
    list_editable = ("is_active",)
    list_filter = ("periodicity", "is_active")
    search_fields = ("title", "chat_id")
    fieldsets = (
        (
            "Основні дані",
            {"fields": ("title", "chat_id")},
        ),
        (
            "Час планування",
            {"fields": ("periodicity", "scheduled_time")},
        ),
        (
            "Формування",
            {
                "fields": (
                    "get_image",
                    "text",
                    "photo",
                    ("button_text", "button_url"),
                    "is_active",
                )
            },
        ),
    ) + BaseAdmin.fieldsets

    @admin.action(description="✅ Активувати вибрані повідомлення")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="❎ Деактивувати вибрані повідомлення")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    def get_image(self, obj):
        """Мініатюра зображення"""
        if obj.photo:
            return mark_safe(
                f'<img src="{obj.photo.url}" height="200" width="auto" alt="Зображення" />'
            )
        return "-"

    get_image.short_description = "Постер"


@admin.register(WeatherNotification)
class WeatherNotificationAdmin(BaseAdmin):
    """Адмін-панель для моделі WeatherNotification."""

    list_display = ("chat_id", "title", "get_image", "is_active")
    list_editable = ("is_active",)
    actions = ["make_active", "make_inactive"]
    search_fields = ("chat_id", "title")
    readonly_fields = ("get_image",) + BaseAdmin.readonly_fields
    save_on_top = True
    save_as = True

    fieldsets = (
        (
            "Основні дані",
            {"fields": ("title", "chat_id", "text", "is_active")},
        ),
        (
            "Зображення",
            {
                "fields": ("poster",),
            },
        ),
    ) + BaseAdmin.fieldsets

    @admin.action(description="✅ Активувати вибране")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="❎ Деактивувати вибране")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    def get_image(self, obj):
        """Мініатюра зображення"""
        if obj.poster:
            return mark_safe(
                f'<img src="{obj.poster.url}" height="30" width="auto" alt="Зображення" />'
            )
        return "-"

    get_image.short_description = "Постер"
