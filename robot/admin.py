from django.contrib import admin
from django.db import IntegrityError

from common.admin import BaseAdmin
from robot.forms import QuizAnswerFormSet
from robot.models import QuizQuestion, QuizAnswer


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    formset = QuizAnswerFormSet
    extra = 3
    min_num = 2
    max_num = 10
    validate_min = True


@admin.register(QuizQuestion)
class QuizQuestionAdmin(BaseAdmin):
    """Адмін-панель моделі QuizQuestion"""

    list_display = (
        "id",
        "text",
        "get_answer_is_correct",
        "created_at",
        "is_active",
    )
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
    )

    def get_answer_is_correct(self, obj):
        return obj.answers.filter(is_correct=True).first().text

    get_answer_is_correct.short_description = "Правильна відповідь"

    def save_related(self, request, form, formsets, change):
        try:
            super().save_related(request, form, formsets, change)
        except IntegrityError as e:
            if "unique_correct_answer" in str(e):
                form.add_error(
                    None, "Може бути лише одна правильна відповідь на питання!"
                )
            else:
                raise

    class Media:
        js = ("adminpanel/js/quiz_admin.js",)
        css = {"all": ("adminpanel/css/quiz_admin.css",)}
