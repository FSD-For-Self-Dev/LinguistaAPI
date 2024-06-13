from aiogram.fsm.state import State, StatesGroup


class Word(StatesGroup):
    language = State()
    new_word = State()
