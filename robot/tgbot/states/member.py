from aiogram.fsm.state import State, StatesGroup


class ProfileStates(StatesGroup):
    """ Стани для заповнення профілю. """

    waiting_for_dob = State()
    waiting_for_phone = State()
