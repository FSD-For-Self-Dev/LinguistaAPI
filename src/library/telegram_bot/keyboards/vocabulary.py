"""Vocabulary keyboards."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

vocabulary_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Поиск'),
            KeyboardButton(text='Сортировка'),
            KeyboardButton(text='Фильтры'),
        ],
        [KeyboardButton(text='Добавить новое слово')],
        [KeyboardButton(text='Добавить несколько новых слов')],
        [KeyboardButton(text='Избранное')],
        [KeyboardButton(text='Вернуться в меню')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)

collection_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Список коллекций')],
        [KeyboardButton(text='Просмотр коллекции')],
        [KeyboardButton(text='Поиск, сортировка, фильтры')],
        [KeyboardButton(text='Создание коллекции')],
        [KeyboardButton(text='Добавление слов в коллекцию')],
        [
            KeyboardButton(
                text='Добавление коллекции в избранное, удаление из избранного'
            )
        ],
        [KeyboardButton(text='Просмотр избранных коллекций')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)
