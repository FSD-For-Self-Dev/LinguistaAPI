from aiogram.types import (KeyboardButton, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
from aiogram.utils.keyboard import ReplyKeyboardBuilder

initial_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Я хочу зарегистрироваться')],
        [KeyboardButton(text='Войти в аккаунт')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Авторизуйтесь или создайте учётную запись',
)


def auth_kb(text: str | list):
    builder = ReplyKeyboardBuilder()
    if isinstance(text, str):
        text = [text]
    [builder.button(txt) for txt in text]
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Отмена')]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)


rmk = ReplyKeyboardRemove()
