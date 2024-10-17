"""Exercises keyboards."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

excercise_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Выбор упражнения (библиотека упражнений)')],
        [KeyboardButton(text='Прохождение упражнения Переводчик')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)
