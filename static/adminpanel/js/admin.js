document.addEventListener("DOMContentLoaded", function () {
    const clientField = document.querySelector("#id_client");
    const cardField = document.querySelector("#id_card_id");

    if (clientField) {
        clientField.addEventListener("change", function () {
            const clientId = this.value;

            if (clientId) {
                fetch(`/bank/api/get_cards/${clientId}/`)
                    .then((response) => response.json())
                    .then((data) => {
                        cardField.innerHTML = "";
                        const defaultOption = document.createElement("option");
                        defaultOption.textContent = "Виберіть картку";
                        defaultOption.value = "";
                        cardField.appendChild(defaultOption);

                        data.cards.forEach((card) => {
                            const option = document.createElement("option");
                            option.value = card.id;
                            option.textContent = card.name;
                            cardField.appendChild(option);
                        });
                    });
            } else {
                cardField.innerHTML = "";
                const defaultOption = document.createElement("option");
                defaultOption.textContent = "Спочатку виберіть клієнта";
                defaultOption.value = "";
                cardField.appendChild(defaultOption);
            }
        });
    }
});
