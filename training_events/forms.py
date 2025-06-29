from django import forms
from .models import TrainingComment, TrainingRating


class TrainingCommentForm(forms.ModelForm):
    class Meta:
        model = TrainingComment
        fields = ["comment", "is_public"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ваш коментар...",
                }
            ),
            "is_public": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }
        labels = {
            "comment": "Коментар",
            "is_public": "Опублікувати коментар",
        }


class TrainingRatingForm(forms.ModelForm):
    class Meta:
        model = TrainingRating
        fields = ["rating"]
        widgets = {
            "rating": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 5,
                    "placeholder": "Оцінка (1-5)",
                }
            ),
        }
        labels = {
            "rating": "Оцінка",
        }
