from django.contrib import admin

from common.admin import BaseAdmin
from training_events.models import (
    TrainingEvent,
    TrainingDistance,
    TrainingRegistration,
)


class TrainingDistanceInline(admin.TabularInline):
    model = TrainingDistance
    extra = 0
    min_num = 1
    max_num = 5
    validate_min = True


@admin.register(TrainingEvent)
class TrainingEventAdmin(BaseAdmin):
    """Клас адмін-панелі для моделі TrainingEvent"""

    save_on_top = True
    save_as = True
    list_display = ["title", "date", "created_by", "location"]
    search_fields = [
        "title",
        "created_by__first_name",
        "created_by__last_name",
    ]
    list_filter = ["date", "created_by", "location", "is_cancelled"]
    inlines = (TrainingDistanceInline,)
    fieldsets = (
        (
            "Основні дані",
            {
                "fields": (
                    "title",
                    "description",
                    "date",
                    "location",
                    "poster",
                    "created_by",
                    "is_cancelled",
                )
            },
        ),
    ) + BaseAdmin.fieldsets


@admin.register(TrainingRegistration)
class TrainingRegistrationAdmin(BaseAdmin):
    """Клас адмін-панелі для моделі TrainingRegistration"""

    list_display = [
        "training",
        "participant",
        "created_at",
        "attendance_confirmed",
        "actual_attendance",
    ]
    search_fields = ["training__title", "participant__username"]
    list_filter = ["training", "participant", "created_at"]
    fieldsets = (
        (
            "Основні дані",
            {
                "fields": (
                    "training",
                    "distance",
                    "participant",
                    "attendance_confirmed",
                    "actual_attendance",
                    "expected_pace",
                    "notes",
                )
            },
        ),
    ) + BaseAdmin.fieldsets