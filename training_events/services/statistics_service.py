from django.utils import timezone
from django.db.models import Sum
from profiles.models import ClubUser
from training_events.models import TrainingEvent


class StatisticsService:
    @staticmethod
    def get_club_statistics():
        """Отримує статистику клубу"""
        now = timezone.now()

        return {
            "total_members": ClubUser.objects.filter(is_active=True).count(),
            "total_trainings": TrainingEvent.objects.filter(
                date__lt=now, is_cancelled=False
            ).count(),
            "total_distance": int(
                TrainingEvent.objects.filter(
                    date__lt=now, is_cancelled=False
                ).aggregate(total=Sum("distances__distance"))["total"]
                or 0
            ),
        }
