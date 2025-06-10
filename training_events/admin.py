from django.contrib import admin
from django.utils.safestring import mark_safe

from common.admin import BaseAdmin
from training_events.enums import TrainingMapProcessingStatusChoices
from training_events.models import (
    TrainingEvent,
    TrainingDistance,
    TrainingRegistration,
    TrainingRating,
    TrainingComment,
)


class TrainingDistanceInline(admin.TabularInline):
    model = TrainingDistance
    extra = 0
    min_num = 1
    max_num = 5
    validate_min = True
    readonly_fields = ("get_route_map_preview", "get_processing_status")

    def get_route_map_preview(self, obj):
        """Мініатюра карти маршруту"""
        if obj and obj.route_gpx_map:
            return mark_safe(
                f'<img src="{obj.route_gpx_map.url}" height="100" width="auto" alt="Карта маршруту" />'
            )
        elif (
            obj
            and obj.route_gpx
            and obj.map_processing_status
            == TrainingMapProcessingStatusChoices.PROCESSING
        ):
            return mark_safe(
                '<span style="color: orange;">⏳ Обробляється...</span>'
            )
        elif (
            obj
            and obj.route_gpx
            and obj.map_processing_status
            == TrainingMapProcessingStatusChoices.PENDING
        ):
            return mark_safe(
                '<span style="color: blue;">⏳ Очікує обробки</span>'
            )
        elif (
            obj
            and obj.route_gpx
            and obj.map_processing_status
            == TrainingMapProcessingStatusChoices.FAILED
        ):
            return mark_safe(
                '<span style="color: red;">❌ Помилка обробки</span>'
            )
        return "-"

    get_route_map_preview.short_description = "Карта маршруту"

    # def get_processing_status(self, obj):
    #     """Статус обробки карти"""
    #     if not obj:
    #         return "-"
    #
    #     status_colors = {
    #         "pending": "blue",
    #         "processing": "orange",
    #         "completed": "green",
    #         "failed": "red",
    #     }
    #
    #     status_labels = {
    #         "pending": "⏳ Очікує",
    #         "processing": "🔄 Обробляється",
    #         "completed": "✅ Готово",
    #         "failed": "❌ Помилка",
    #     }
    #
    #     color = status_colors.get(obj.map_processing_status, "gray")
    #     label = status_labels.get(
    #         obj.map_processing_status, obj.map_processing_status
    #     )
    #
    #     return mark_safe(f'<span style="color: {color};">{label}</span>')
    #
    # get_processing_status.short_description = "Статус карти"


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
        "is_feedback_sent",
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
        "is_feedback_sent",
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
                    "is_feedback_sent",
                    "is_cancelled",
                    "cancellation_reason",
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


@admin.register(TrainingRating)
class TrainingRatingAdmin(BaseAdmin):
    """Клас адмін-панелі для моделі TrainingRating"""

    readonly_fields = ("created_at", "updated_at")
    list_display = ["training", "participant", "rating", "created_at"]
    search_fields = ["training__title", "participant__username"]
    list_filter = ["training", "participant", "created_at"]
    fieldsets = (
        (
            "Основні дані",
            {"fields": ("training", "participant", "rating")},
        ),
    ) + BaseAdmin.fieldsets


@admin.register(TrainingComment)
class TrainingCommentAdmin(BaseAdmin):
    """Клас адмін-панелі для моделі TrainingComment"""

    readonly_fields = ("created_at", "updated_at")
    list_display = ["training", "participant", "created_at"]
    search_fields = ["training__title", "participant__username"]
    list_filter = ["training", "participant", "created_at"]
    fieldsets = (
        (
            "Основні дані",
            {"fields": ("training", "participant", "comment", "is_public")},
        ),
    ) + BaseAdmin.fieldsets
