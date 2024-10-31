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

word_profile_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Редактировать')],
        # [KeyboardButton(text='Тренировать')],
        # [KeyboardButton(text='Поделиться')],
        [KeyboardButton(text='Удалить')],
        [KeyboardButton(text='Вернуться назад')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)

collections_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='Поиск'),
            KeyboardButton(text='Сортировка'),
            KeyboardButton(text='Фильтры'),
        ],
        [KeyboardButton(text='Создать коллекцию')],
        [KeyboardButton(text='Избранное')],
        [KeyboardButton(text='Вернуться в меню')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)

collection_profile_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Редактировать')],
        [KeyboardButton(text='Добавить слова')],
        # [KeyboardButton(text='Тренировать')],
        # [KeyboardButton(text='Поделиться')],
        [KeyboardButton(text='Удалить')],
        [KeyboardButton(text='Вернуться назад')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)
