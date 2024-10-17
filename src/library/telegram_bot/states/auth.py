"""Authentication states."""

from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    username = State()
    email = State()
    password1 = State()
    password2 = State()


class Authorization(StatesGroup):
    username = State()
    email = State()
    password = State()


class Authorized(StatesGroup):
    token = State()
