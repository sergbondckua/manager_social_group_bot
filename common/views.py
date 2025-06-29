from django.views import generic

from training_events.services.statistics_service import StatisticsService
from training_events.services.training_service import TrainingService


class HomeView(generic.TemplateView):
    """Головна сторінка."""

    template_name = "club/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Найближчі тренування (максимум 6)
        context["upcoming_trainings"] = (
            TrainingService.get_upcoming_trainings(limit=6)
        )

        # Загальна статистика клубу
        context.update(StatisticsService.get_club_statistics())
        return context
