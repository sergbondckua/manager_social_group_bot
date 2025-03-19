from django.contrib import admin

from common.admin import BaseAdmin
from robot.forms import QuizAnswerFormSet
from robot.models import QuizQuestion, QuizAnswer


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    formset = QuizAnswerFormSet
    extra = 5
    min_num = 2
    validate_min = True


@admin.register(QuizQuestion)
class QuizQuestionAdmin(BaseAdmin):
    """Адмін-панель моделі QuizQuestion"""

    list_display = ("id", "text", "created_at", "is_active")
    list_display_links = ("id", "text")
    inlines = (QuizAnswerInline,)
    readonly_fields = ("id", "created_at", "updated_at")
    search_fields = ("text",)
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    ordering = ("created_at",)
    save_on_top = True
    save_as = True
    fieldsets = (
        (
            "Основні дані",
            {"fields": ("text", "explanation", "image", "is_active")},
        ),
    ) + BaseAdmin.fieldsets

    class Media:
        # js = ("adminpanel/js/quiz_admin.js",)
        pass