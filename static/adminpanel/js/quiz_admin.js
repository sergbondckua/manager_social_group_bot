document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('quizquestion_form');
    if (!form) return;

    // Селектор для всіх активних рядків (адаптовано для Django 5.1.5)
    const rowSelector = '.inline-related.dynamic-robot_quizanswer:not(.empty-form)';

    function validateForm(event) {
        let validAnswers = 0;
        let correctAnswers = 0;
        const errorMessages = [];

        document.querySelectorAll(rowSelector).forEach(row => {
            const textInput = row.querySelector('input[id$="-text"]');
            const isCorrect = row.querySelector('input[id$="-is_correct"]');
            const deleteCheckbox = row.querySelector('input[id$="-DELETE"]');

            // Перевірка активного рядка
            if (!deleteCheckbox?.checked && textInput?.value.trim().length > 0) {
                validAnswers++;
                if (isCorrect?.checked) correctAnswers++;
            }
        });

        // Валідація
        if (validAnswers < 2) errorMessages.push('Необхідно мінімум дві відповіді');
        if (correctAnswers !== 1) errorMessages.push('Повинна бути рівно одна правильна відповідь');

        // Показ помилок
        showErrors(errorMessages);

        if (errorMessages.length > 0 && event.type === 'submit') {
            event.preventDefault();
            return false;
        }
    }

    function showErrors(messages) {
        // Видалення старих помилок
        const oldErrors = form.querySelectorAll('.custom-validation-error');
        oldErrors.forEach(e => e.remove());

        // Додаємо нові помилки
        if (messages.length > 0) {
            const errorHTML = `
                <div class="custom-validation-error" style="margin:20px 0; padding:15px; background:#fff0f0; border-left:4px solid #ba2121">
                    <strong>Помилки:</strong>
                    <ul style="margin:10px 0 0 20px">${messages.map(m => `<li>${m}</li>`).join('')}</ul>
                </div>
            `;
            form.insertAdjacentHTML('afterbegin', errorHTML);
        }
    }

    // Автоматичне оновлення чекбоксів
    form.addEventListener('change', function(e) {
        if (e.target.matches('input[id$="-is_correct"]')) {
            if (e.target.checked) {
                document.querySelectorAll('input[id$="-is_correct"]').forEach(checkbox => {
                    if (checkbox !== e.target) checkbox.checked = false;
                });
            }
            validateForm(e); // Миттєва валідація
        }
    });

    // Обробник події вводу тексту
    form.addEventListener('input', function(e) {
        if (e.target.matches('input[id$="-text"]')) {
            validateForm(e);
        }
    });

    // Обробник додавання нового рядка
    document.querySelector('.add-row a').addEventListener('click', function() {
        setTimeout(() => {
            validateForm(new Event('init'));
        }, 100);
    });

    form.addEventListener('submit', validateForm);
    validateForm(new Event('init')); // Первинна перевірка
});