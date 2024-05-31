from aiogram.fsm.state import State, StatesGroup


class NewLanguage(StatesGroup):
    new_language = State()