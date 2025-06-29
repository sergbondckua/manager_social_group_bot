from datetime import timedelta
from django.db.models import Count, Sum
from django.utils import timezone
from training_events.models import TrainingEvent


class TrainingService:
    """Сервіс для роботи з тренуваннями"""

    @staticmethod
    def get_upcoming_trainings(limit: int = None):
        """Отримує найближчі тренування з учасниками
        Args:
            limit (int, optional): Ліміт тренувань.
        """
        now = timezone.now()

        trainings = (
            TrainingEvent.objects.filter(date__gt=now, is_cancelled=False)
            .select_related("created_by")
            .prefetch_related(
                "distances", "registrations", "registrations__participant"
            )
            .annotate(
                participants_count=Count("registrations", distinct=True),
                max_participants_total=Sum("distances__max_participants"),
            )
            .order_by("date")
        )

        trainings = trainings[:limit] if limit is not None else trainings

        for training in trainings:
            TrainingService._enrich_training_data(training)

        return trainings

    @staticmethod
    def _enrich_training_data(training):
        """Додає додаткові обчислені поля до тренування"""

        # Обчислення максимальної кількості учасників
        max_participants = (
            sum(
                distance.max_participants
                for distance in training.distances.all()
                if distance.max_participants != 0
            )
            or 0
        )

        training.max_participants = max_participants
        training.participants = [
            reg.participant for reg in training.registrations.all()
        ]  # список учасників
        distances = [str(d.distance) for d in training.distances.all()]
        training.distance = (
            " | ".join(distances) + " км" if distances else "TBD"
        )  # список дистанцій
        training.is_full = (
            training.max_participants == training.participants_count
        )  # чи тренування повне
