from aiogram.fsm.state import StatesGroup, State


class RegistrationForm(StatesGroup):
    username = State()
    email = State()
    password1 = State()
    password2 = State()


class AuthForm(StatesGroup):
    username = State()
    password = State()
    token = State()
