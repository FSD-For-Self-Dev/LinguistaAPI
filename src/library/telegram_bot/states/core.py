"""Core states."""

from aiogram.fsm.state import State, StatesGroup


class PreviousState(StatesGroup):
    previous_state_handler = State()
