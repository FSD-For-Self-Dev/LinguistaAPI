"""Core states."""

from aiogram.fsm.state import State, StatesGroup


class Core(StatesGroup):
    choose_page_num = State()
