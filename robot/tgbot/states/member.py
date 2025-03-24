from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    """Стани для заповнення профілю."""

    waiting_field_input = State()
