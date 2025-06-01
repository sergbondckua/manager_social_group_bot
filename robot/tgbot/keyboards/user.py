from aiogram.utils.keyboard import InlineKeyboardBuilder

def distance_keyboard(distances):
    builder = InlineKeyboardBuilder()
    for item in distances:
        distance = item["distance"]
        training_id = item["training_id"]
        distance_id = item["distance_id"]
        builder.button(
            text=f"{distance} км",
            callback_data=f"distance_{training_id}_{distance_id}",
        )
    builder.button(
            text="❌ Прибрати",
            callback_data="btn_close",
        ),
    builder.adjust(2, 1)
    return builder.as_markup()

def btn_close_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
            text="❌ Прибрати",
            callback_data="btn_close",
        ),
    return builder.as_markup()
