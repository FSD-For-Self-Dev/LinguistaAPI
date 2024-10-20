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
return_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Вернуться назад')]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

cancel_button = InlineKeyboardButton(text='Отмена', callback_data='cancel')
cancel_inline_kb = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])

forward_button = InlineKeyboardButton(text='Вперед', callback_data='forward')
backward_button = InlineKeyboardButton(text='Назад', callback_data='backward')


def get_page_num_button(page_num: int, pages_total_amount: int) -> InlineKeyboardButton:
    """Returns button to choose page."""
    return InlineKeyboardButton(
        text=f'{page_num}/{pages_total_amount}', callback_data='choose_page'
    )
