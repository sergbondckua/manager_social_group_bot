from aiogram.fsm.state import StatesGroup, State


class CreateTraining(StatesGroup):
    """Стани FSM для створення тренування."""

    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_location = State()
    waiting_for_distance = State()
    waiting_for_pace_min = State()
    waiting_for_pace_max = State()
    waiting_for_max_participants = State()
    waiting_for_poster = State()
    waiting_for_route_gpx = State()
    confirm = State()
