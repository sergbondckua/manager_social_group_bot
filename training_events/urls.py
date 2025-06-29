from django.urls import path
from training_events import views


urlpatterns = [
    path(
        "<int:pk>",
        views.TrainingDetailView.as_view(),
        name="training_detail",
    ),
    path(
        "<int:pk>/register/",
        views.TrainingRegisterView.as_view(),
        name="training_register",
    ),
    path(
        "<int:pk>/unregister/",
        views.TrainingUnregisterView.as_view(),
        name="training_unregister",
    ),
    path(
        "<int:pk>/add-rating/",
        views.AddTrainingRatingView.as_view(),
        name="add_training_rating",
    ),
    path(
        "<int:pk>/add-comment/",
        views.AddTrainingCommentView.as_view(),
        name="add_training_comment",
    ),
    path("", views.TrainingListView.as_view(), name="training_list"),
]

app_name = "training_events"
