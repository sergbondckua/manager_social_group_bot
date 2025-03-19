from django.contrib import admin
from django.db import models
from django.utils.safestring import mark_safe
from tinymce.widgets import TinyMCE

from common.models import Compliment, Greeting


class BaseAdmin(admin.ModelAdmin):
    """Основна модель-робоча частина адмін-панелі"""

    formfield_overrides = {
        models.TextField: {"widget": TinyMCE()},
    }

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Інформація запису",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(Compliment)
class ComplimentAdmin(BaseAdmin):
    list_display = ("html_text", "created_at")
    search_fields = ("text",)
    save_as = True
    save_on_top = True
    ordering = ("-created_at",)
    fieldsets = (
        (
            "Основні дані",
            {"fields": ("text",)},
        ),
    ) + BaseAdmin.fieldsets

    def html_text(self, obj):
        return mark_safe(obj.text)

    html_text.short_description = "Текст компліменту"


@admin.register(Greeting)
class GreetingAdmin(BaseAdmin):
    list_display = ("html_text", "created_at", "is_active")
    search_fields = ("text", "event_type")
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    save_as = True
    save_on_top = True
    fieldsets = (
        (
            "Основні дані",
            {"fields": ("event_type", "text", "is_active")},
        ),
    ) + BaseAdmin.fieldsets

    def html_text(self, obj):
        return mark_safe(obj.text)

    html_text.short_description = "Текст привітання"
