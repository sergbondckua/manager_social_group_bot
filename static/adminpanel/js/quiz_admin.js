document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('quizquestion_form');
    const answersContainer = document.querySelector('#quizquestion_form .inline-related');

    function validateForm(event) {
        let validAnswers = 0;
        let correctAnswers = 0;
        const errorMessages = [];

        // Перевіряємо всі рядки відповідей
        document.querySelectorAll('.inline-related:not(.empty-form)').forEach(row => {
            const textInput = row.querySelector('input[name$="-text"]');
            const isCorrect = row.querySelector('input[name$="-is_correct"]');
            const isDeleted = row.querySelector('input[name$="-DELETE"]');

            if (!isDeleted || !isDeleted.checked) {
                if (textInput && textInput.value.trim().length > 0) {
                    validAnswers++;
                }
                if (isCorrect && isCorrect.checked) {
                    correctAnswers++;
                }
            }
        });

        // Валідація мінімальної кількості
        if (validAnswers < 2) {
            errorMessages.push('Потрібно щонайменше дві відповіді');
        }

        // Валідація правильної відповіді
        if (correctAnswers !== 1) {
            errorMessages.push('Повинна бути тільки одна правильна відповідь');
        }

        // Показуємо помилки
        showErrors(errorMessages);

        if (errorMessages.length > 0) {
            event.preventDefault();
            return false;
        }
    }

    function showErrors(messages) {
        // Видаляємо старі помилки
        document.querySelectorAll('.custom-validation-error').forEach(el => el.remove());

        // Додаємо нові помилки
        if (messages.length > 0) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'custom-validation-error errornote';
            errorDiv.innerHTML = `<strong>Помилки:</strong><ul>${messages.map(m => `<li>${m}</li>`).join('')}</ul>`;
            form.insertBefore(errorDiv, form.firstChild);
        }
    }

    if (form) {
        form.addEventListener('submit', validateForm);

        // Додаємо обробники подій для динамічних рядків
        answersContainer.addEventListener('change', function (e) {
            if (e.target.matches('input[type="checkbox"][name$="-is_correct"]')) {
                // При виборі правильної відповіді знімаємо інші
                document.querySelectorAll('input[type="checkbox"][name$="-is_correct"]').forEach(checkbox => {
                    if (checkbox !== e.target) {
                        checkbox.checked = false;
                    }
                });
            }
        });
    }
});