from django import forms
from django.core.exceptions import ValidationError


class QuizAnswerFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        # Відфільтровуємо видалені та порожні форми
        valid_answers = [
            form
            for form in self.forms
            if not form.cleaned_data.get("DELETE", False)
            and form.cleaned_data.get("text")
        ]

        # Перевірка мінімальної кількості відповідей
        if len(valid_answers) < 2:
            raise ValidationError("Необхідно додати щонайменше дві відповіді.")

        # Перевірка кількості правильних відповідей
        correct_count = sum(
            1
            for form in valid_answers
            if form.cleaned_data.get("is_correct", False)
        )

        if correct_count != 1:
            raise ValidationError(
                "Повинна бути тільки одна правильна відповідь."
            )

        # Перевірка наявності хоча б однієї правильної відповіді
        if correct_count < 1:
            raise ValidationError("Повинна бути хоча б одна правильна відповідь.")
