from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# стартовая клавиатура
initial_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Я хочу зарегистрироваться')],
        [KeyboardButton(text='Войти в аккаунт')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Авторизуйтесь или создайте учётную запись',
)

# главная клавиатура
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

# клавиатура профиля
profile_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Добавить родной язык')],
        [KeyboardButton(text='Добавить изучаемый язык')],
        [KeyboardButton(text='Просмотр профиля')],
        [KeyboardButton(text='Вернуться в главное меню')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)

# главная клавитура словаря
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

# главная клавитура коллекий
collection_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Список коллекций')],
        [KeyboardButton(text='Просмотр коллекции')],
        [KeyboardButton(text='Поиск, сортировка, фильтры')],
        [KeyboardButton(text='Создание коллекции')],
        [KeyboardButton(text='Добавление слов в коллекцию')],
        [KeyboardButton(text='Добавление коллекции в избранное, удаление из избранного')],
        [KeyboardButton(text='Просмотр избранных коллекций')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)

# главная клавитура упражнений
excercise_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Выбор упражнения (библиотека упражнений)')],
        [KeyboardButton(text='Прохождение упражнения Переводчик')],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Выберите пункт меню',
)

def auth_kb(text: str | list):
    builder = ReplyKeyboardBuilder()
    if isinstance(text, str):
        text = [text]
    [builder.button(txt) for txt in text]
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

# клавитатура отмены?
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Отмена')]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

# удаление клавиатуры
rmk = ReplyKeyboardRemove()
