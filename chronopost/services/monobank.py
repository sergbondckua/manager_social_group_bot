import requests

MONOBANK_BASE_URL = "https://api.monobank.ua/api/merchant/invoice/create"
MONOBANK_TOKEN = "ucadxHvlLD7wM51h4MvU3MsubtaQv6n7PyA0mNQa1ATU"

amount = 100  # Сума в копійках (100 грн = 10000 копійок)
description = "Оплата абонементу клубу"

# Генерація платіжного запиту
invoice_data = {
    "amount": amount,
    "ccy": 980,  # Код валюти UAH
    "merchantPaymInfo": {
        "reference": f"user_",
        "destination": description,
        "comment": "Покупка щастя",
        "basketOrder": [
            {
                "name": "Абонемент",
                "qty": 1,
                "sum": 100,
                "total": 200,
                "icon": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT49z8lUjTCjo8ewHD8sMJ2UUCIlmjN6AiDXA&s",
                "unit": "шт.",
                "code": "d21da1c47f3c45fca10a10c32518bdeb",
            }
        ],
    },
    "redirectUrl": "https://club.crossrunche.com/",
}
headers = {"X-Token": MONOBANK_TOKEN, "X-Cms": "CrossRunChePay"}
response = requests.post(MONOBANK_BASE_URL, json=invoice_data, headers=headers)

if response.status_code == 200:
    invoice_url = response.json().get("pageUrl")
    print(response.json())
    print(f"Платіжна сторінка: {invoice_url}")
else:
    print("Виникла помилка при створенні платежу.")


if __name__ == "__main__":
    pass
