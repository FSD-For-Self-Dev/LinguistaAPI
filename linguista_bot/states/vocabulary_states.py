from aiogram.fsm.state import State, StatesGroup


class NewWord(StatesGroup):
    new_word = State()