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
    keyboard=[[KeyboardButton(text='Отменить')]],
    resize_keyboard=True,
    one_time_keyboard=True,
)
return_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Вернуться назад')]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

cancel_button = InlineKeyboardButton(text='Отменить', callback_data='cancel')
cancel_inline_kb = InlineKeyboardMarkup(inline_keyboard=[[cancel_button]])

return_button = InlineKeyboardButton(text='Вернуться назад', callback_data='return')
return_inline_kb = InlineKeyboardMarkup(inline_keyboard=[[return_button]])

forward_button = InlineKeyboardButton(text='Вперед', callback_data='forward')
backward_button = InlineKeyboardButton(text='Назад', callback_data='backward')


def get_page_num_button(
    page_num: int, pages_total_amount: int, callback_data: str = 'choose_page'
) -> InlineKeyboardButton:
    """Returns button to choose page."""
    return InlineKeyboardButton(
        text=f'{page_num}/{pages_total_amount}', callback_data=callback_data
    )


def get_forward_button(callback_data: str = 'forward') -> InlineKeyboardButton:
    """Returns button to get next page."""
    return InlineKeyboardButton(text='Вперед', callback_data=callback_data)


def get_backward_button(callback_data: str = 'backward') -> InlineKeyboardButton:
    """Returns button to get previous page."""
    return InlineKeyboardButton(text='Назад', callback_data=callback_data)


nested_object_already_exist_inlin_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text='Обновить',
                callback_data='word_create_existing_nested__update',
            ),
        ],
        [
            InlineKeyboardButton(
                text='Взять из словаря',
                callback_data='word_create_existing_nested__get',
            ),
        ],
        [
            cancel_button,
        ],
    ]
)
