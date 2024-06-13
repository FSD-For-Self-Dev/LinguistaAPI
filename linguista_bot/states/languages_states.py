from aiogram.fsm.state import State, StatesGroup


class Language(StatesGroup):
    language_to_learn = State()
    language_to_remove = State()
