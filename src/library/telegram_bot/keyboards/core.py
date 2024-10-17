"""Core keyboards."""

from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

initial_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Зарегистрироваться')],
        [KeyboardButton(text='Войти в аккаунт')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Авторизуйтесь или создайте учётную запись',
)

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Профиль')],
        [KeyboardButton(text='Словарь')],
        [KeyboardButton(text='Коллекции')],
        [KeyboardButton(text='Упражнения')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Отмена')]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

cancel_button = InlineKeyboardButton(text='Отмена', callback_data='cancel')
cancel_inline_kb = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])
