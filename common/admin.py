from django.contrib import admin


class BaseAdmin(admin.ModelAdmin):
    """Основна модель-робоча частина адмін-панелі"""

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
