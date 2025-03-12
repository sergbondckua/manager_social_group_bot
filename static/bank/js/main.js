/* DataTables initialization */

$(document).ready(function () {
    $('#statement').DataTable({
        paging: true,
        pageLength: 50,
        searching: true,
        order: [[1, 'desc']],
        language: {
            url: 'https://cdn.datatables.net/plug-ins/1.13.4/i18n/uk.json',
            decimal: ',',
            thousands: ' ',
        },
        columnDefs: [
            {
                targets: 0,
                orderable: false,
                searchable: false
            },
            {
                targets: 3,
                render: function (data) {
                    let num = parseFloat(data);
                    let formattedNum = num.toLocaleString('uk-UA', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    });

                    // Додаємо стилі залежно від значення
                    if (num < 0) {
                        return `<span style="color: red;">${formattedNum}</span>`;
                    } else if (num > 400) {
                        return `<span style="color: green;">${formattedNum}</span>`;
                    }
                    return formattedNum;
                }
            },
            {
                targets: 6,
                render: function (data) {
                    let num = parseFloat(data);
                    return num.toLocaleString('uk-UA', {minimumFractionDigits: 2, maximumFractionDigits: 2});
                }
            },


        ]
    });
});

/* Monobank Statement initialization */
function updateCards(clientSelect) {
    const clientId = clientSelect.value;
    const cardField = document.getElementById("id_card_id");

    if (!clientId) {
        cardField.innerHTML = "<option value=''>--- Зпочатку оберіть клієнта ---</option>";
        return;
    }

    fetch(`/bank/api/get-cards/${clientId}/`)
        .then(response => response.json())
        .then(data => {
            cardField.innerHTML = ""; // Очищаємо старі опції
            data.cards.forEach(card => {
                const option = document.createElement("option");
                option.value = card.card_id;
                option.textContent = card.card_id;
                cardField.appendChild(option);
            });

            // Якщо є початкове значення для card_id, вибираємо його
            const initialCardId = cardField.dataset.initialValue;
            if (initialCardId) {
                cardField.value = initialCardId;
            }
        })
        .catch(error => {
            console.error("Помилка при завантаженні карток:", error);
        });
}

document.addEventListener("DOMContentLoaded", function () {
    const clientSelect = document.getElementById("id_client_token");
    if (clientSelect && clientSelect.value) {
        updateCards(clientSelect);
    }
});