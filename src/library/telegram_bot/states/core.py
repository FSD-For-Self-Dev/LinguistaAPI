"""Core states."""

from aiogram.fsm.state import State, StatesGroup


class PreviousState(StatesGroup):
    previous_state_handler = State()


class User(StatesGroup):
    learning_languages_info = State()
    native_languages_info = State()
    words_count = State()
