from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    """Стани для заповнення профілю."""

    waiting_field_input = State()


class TrainingCommentStates(StatesGroup):
    """Стани для коментарів до тренування."""

    waiting_for_comment = State()
