"""User profile keyboards."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

profile_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Добавить изучаемый язык')],
        [KeyboardButton(text='Редактировать профиль')],
        [KeyboardButton(text='Выйти из аккаунта')],
        [KeyboardButton(text='Вернуться в меню')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)


profile_update_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Обновить фото профиля')],
        [KeyboardButton(text='Изменить родные языки')],
        [KeyboardButton(text='Изменить имя')],
        [KeyboardButton(text='Вернуться назад')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)
