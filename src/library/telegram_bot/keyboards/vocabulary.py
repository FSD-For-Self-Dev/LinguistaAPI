"""Vocabulary keyboards."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

vocabulary_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Просмотр словаря')],
        [KeyboardButton(text='Поиск по словарю, сортировка, фильтры')],
        [KeyboardButton(text='Просмотр профиля слова')],
        [KeyboardButton(text='Добавление одного слова')],
        [KeyboardButton(text='Добавление нескольких слов')],
        [KeyboardButton(text='Добавление слов в избранное, удаление из избранного')],
        [KeyboardButton(text='Просмотр избранных слов')],
        [KeyboardButton(text='Добавление дополнений к слову')],
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
