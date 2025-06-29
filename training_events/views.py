from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import DetailView, View, ListView

from training_events.forms import TrainingCommentForm, TrainingRatingForm
from training_events.models import (
    TrainingEvent,
    TrainingRegistration,
    TrainingComment,
    TrainingRating,
    TrainingDistance,
)


class TrainingDetailView(DetailView):
    """Детальна інформація про тренування."""

    model = TrainingEvent
    template_name = "training_events/training_detail.html"
    context_object_name = "training"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        training = self.object

        registrations = training.registrations.select_related(
            "participant", "distance"
        )
        context["participants_count"] = registrations.count()

        ratings = training.ratings.all()
        context["average_rating"] = ratings.aggregate(Avg("rating"))[
            "rating__avg"
        ]
        context["ratings_count"] = ratings.count()

        context["comments"] = (
            training.comments.filter(is_public=True)
            .select_related("participant")
            .order_by("-created_at")
        )

        user = self.request.user
        user_registration = None
        user_rating = None
        user_comment = None
        can_rate_and_comment = False

        if user.is_authenticated:
            try:
                user_registration = registrations.get(participant=user)
                can_rate_and_comment = training.is_past

                if can_rate_and_comment:
                    user_rating = training.ratings.filter(
                        participant=user
                    ).first()
                    user_comment = training.comments.filter(
                        participant=user
                    ).first()
            except TrainingRegistration.DoesNotExist:
                pass

        context.update(
            {
                "user_registration": user_registration,
                "user_rating": user_rating,
                "user_comment": user_comment,
                "can_rate_and_comment": can_rate_and_comment,
                "rating_form": TrainingRatingForm(),
                "comment_form": TrainingCommentForm(),
                "distances_with_participants": [
                    {
                        "distance": distance,
                        "participants": registrations.filter(
                            distance=distance
                        ),
                        "count": registrations.filter(
                            distance=distance
                        ).count(),
                    }
                    for distance in training.available_distances
                ],
            }
        )
        return context


@method_decorator(csrf_protect, name="dispatch")
class TrainingRegisterView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        training = get_object_or_404(TrainingEvent, id=self.kwargs["pk"])
        distance_id = request.POST.get("distance_id")

        if not distance_id:
            messages.error(request, "Будь ласка, оберіть дистанцію")
            return redirect("training_events:training_detail", pk=training.id)

        distance = get_object_or_404(training.distances, id=distance_id)

        if training.is_past or training.is_cancelled:
            messages.error(
                request, "Неможливо зареєструватися на це тренування"
            )
            return redirect(
                "training_events:training_events:training_detail",
                pk=training.id,
            )

        if 0 < distance.max_participants <= distance.registrations.count():
            messages.error(request, "На цій дистанції вже немає вільних місць")
            return redirect("training_events:training_detail", pk=training.id)

        registration, created = TrainingRegistration.objects.get_or_create(
            training=training,
            participant=request.user,
            defaults={"distance": distance},
        )

        if created:
            messages.success(
                request,
                f'Ви успішно зареєструвалися на тренування "{training.title}"',
            )
        else:
            if registration.distance != distance:
                registration.distance = distance
                registration.save()
                messages.success(request, "Вашу реєстрацію оновлено")
            else:
                messages.info(request, "Ви вже зареєстровані на це тренування")

        return redirect("training_events:training_detail", pk=training.id)


@method_decorator(csrf_protect, name="dispatch")
class TrainingUnregisterView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        training = get_object_or_404(TrainingEvent, id=self.kwargs["pk"])

        try:
            registration = TrainingRegistration.objects.get(
                training=training, participant=request.user
            )
            registration.delete()
            messages.success(request, "Вашу реєстрацію скасовано")
        except TrainingRegistration.DoesNotExist:
            messages.error(request, "Ви не зареєстровані на це тренування")

        return redirect("training_events:training_detail", pk=training.id)


@method_decorator(csrf_protect, name="dispatch")
class AddTrainingRatingView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        training = get_object_or_404(TrainingEvent, id=self.kwargs["pk"])

        if not training.is_past:
            messages.error(
                request, "Ви можете оцінювати тільки завершені тренування"
            )
            return redirect("training_events:training_detail", pk=training.id)

        form = TrainingRatingForm(request.POST)
        if form.is_valid():
            rating, created = TrainingRating.objects.get_or_create(
                training=training,
                participant=request.user,
                defaults={"rating": form.cleaned_data["rating"]},
            )

            if not created:
                rating.rating = form.cleaned_data["rating"]
                rating.save()
                messages.success(request, "Вашу оцінку оновлено")
            else:
                messages.success(request, "Дякуємо за вашу оцінку!")
        else:
            messages.error(request, "Помилка при збереженні оцінки")

        return redirect("training_events:training_detail", pk=training.id)


@method_decorator(csrf_protect, name="dispatch")
class AddTrainingCommentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        training = get_object_or_404(TrainingEvent, id=self.kwargs["pk"])

        if not training.is_past:
            messages.error(
                request,
                "Ви можете коментувати тільки завершені тренування",
            )
            return redirect("training_events:training_detail", pk=training.id)

        form = TrainingCommentForm(request.POST)
        if form.is_valid():
            comment, created = TrainingComment.objects.get_or_create(
                training=training,
                participant=request.user,
                defaults={
                    "comment": form.cleaned_data["comment"],
                    "is_public": form.cleaned_data["is_public"],
                },
            )

            if not created:
                comment.comment = form.cleaned_data["comment"]
                comment.is_public = form.cleaned_data["is_public"]
                comment.save()
                messages.success(request, "Ваш коментар оновлено")
            else:
                messages.success(request, "Дякуємо за ваш відгук!")
        else:
            messages.error(request, "Помилка при збереженні коментаря")

        return redirect("training_events:training_detail", pk=training.id)


class TrainingListView(ListView):
    """Відображення списку всіх тренувань з пошуком та фільтрацією"""

    model = TrainingEvent
    template_name = "training_events/training_list.html"
    context_object_name = "trainings"
    paginate_by = 10
    ordering = ["date"]

    def get_queryset(self):
        queryset = (
            TrainingEvent.objects.select_related("created_by")
            .prefetch_related("distances", "registrations", "ratings")
        ).order_by("-date")

        # Фільтрація за статусом
        status = self.request.GET.get("status")
        if status == "upcoming":
            queryset = queryset.filter(
                date__gte=timezone.now(), is_cancelled=False
            )
        elif status == "past":
            queryset = queryset.filter(date__lt=timezone.now())
        elif status == "cancelled":
            queryset = queryset.filter(is_cancelled=True)
        elif status == "active":
            queryset = queryset.filter(
                date__gte=timezone.now(), is_cancelled=False
            )

        # Пошук
        search_query = self.request.GET.get("search")
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(location__icontains=search_query)
                | Q(created_by__first_name__icontains=search_query)
                | Q(created_by__last_name__icontains=search_query)
            )

        # Фільтрація за місцем
        location = self.request.GET.get("location")
        if location:
            queryset = queryset.filter(location__icontains=location)

        # Фільтрація за організатором
        organizer = self.request.GET.get("organizer")
        if organizer:
            queryset = queryset.filter(created_by__id=organizer)

        # Фільтрація за дистанцією
        distance = self.request.GET.get("distance")
        if distance:
            # Заміна коми на крапку
            distance = distance.replace(",", ".")
            distance = float(distance)
            queryset = queryset.filter(distances__distance=distance)

        # Фільтрація за датою
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Передаємо параметри пошуку в контекст для збереження в формі
        context["search_query"] = self.request.GET.get("search", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_location"] = self.request.GET.get("location", "")
        context["selected_organizer"] = self.request.GET.get("organizer", "")
        context["selected_distance"] = self.request.GET.get("distance", "")
        context["date_from"] = self.request.GET.get("date_from", "")
        context["date_to"] = self.request.GET.get("date_to", "")

        # Додаємо статистику
        context["total_trainings"] = TrainingEvent.objects.count()
        context["upcoming_trainings"] = TrainingEvent.objects.filter(
            date__gte=timezone.now(), is_cancelled=False
        ).count()
        context["past_trainings"] = TrainingEvent.objects.filter(
            date__lt=timezone.now()
        ).count()

        # Унікальні локації для фільтра
        context["locations"] = (
            TrainingEvent.objects.values_list("location", flat=True)
            .distinct()
            .order_by("location")
        )

        # Унікальні дистанції для фільтра
        context["distances"] = (
            TrainingDistance.objects.values_list("distance", flat=True)
            .distinct()
            .order_by("distance")
        )

        # Організатори для фільтра
        context["organizers"] = (
            TrainingEvent.objects.select_related("created_by")
            .values(
                "created_by__id",
                "created_by__first_name",
                "created_by__last_name",
            )
            .distinct()
            .order_by("created_by__first_name")
        )

        return context
