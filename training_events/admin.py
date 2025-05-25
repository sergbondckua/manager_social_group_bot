from django.contrib import admin
from django.utils.safestring import mark_safe

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
    readonly_fields = ("get_image",) + BaseAdmin.readonly_fields
    list_display = [
        "title_and_location",
        "date",
        "created_by",
        "get_distances",
        "get_participant_count",
        "is_cancelled",
    ]
    search_fields = [
        "title",
        "created_by__first_name",
        "created_by__last_name",
    ]
    list_filter = [
        "date",
        "created_by",
        "location",
        "created_by",
        "is_cancelled",
    ]
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
                    "get_image",
                    "created_by",
                    "is_cancelled",
                )
            },
        ),
    ) + BaseAdmin.fieldsets

    def get_image(self, obj):
        """Мініатюра зображення"""
        if obj.poster:
            return mark_safe(
                f'<img src="{obj.poster.url}" height="200" width="auto" alt="Зображення" />'
            )
        return "-"

    get_image.short_description = "Прев'ю"

    def get_distances(self, obj):
        return ", ".join([f"{d.distance} км" for d in obj.available_distances])

    get_distances.short_description = "Дистанції"

    def get_participant_count(self, obj):
        return obj.participant_count

    get_participant_count.short_description = "Зареєстровано"

    def title_and_location(self, obj):
        return f"{obj.title} - {obj.location}"

    title_and_location.short_description = "Назва і місце"


@admin.register(TrainingRegistration)
class TrainingRegistrationAdmin(BaseAdmin):
    """Клас адмін-панелі для моделі TrainingRegistration"""

    list_display = [
        "training",
        "participant",
        "distance",
        "created_at",
        "attendance_confirmed",
        "actual_attendance",
    ]
    search_fields = ["training__title", "participant__username"]
    list_filter = [
        "training",
        "participant",
        "created_at",
        "attendance_confirmed",
        "actual_attendance",
    ]
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
