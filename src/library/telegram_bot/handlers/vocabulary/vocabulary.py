"""Vocabulary handlers."""

import os
import logging
import math
from http import HTTPStatus

import aiohttp
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BufferedInputFile,
    CallbackQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from keyboards.core import (
    cancel_inline_kb,
    forward_button,
    backward_button,
    get_page_num_button,
)
from keyboards.vocabulary import vocabulary_kb
from states.vocabulary import Vocabulary
from states.core import User
from handlers.urls import VOCABULARY_URL, LEARNING_LANGUAGES_URL, TYPES_URL
from handlers.utils import (
    send_error_message,
    api_request_logging,
    get_authentication_headers,
    send_unauthorized_response,
)

from .constants import (
    words_ordering_pretty,
    ordering_type_pretty,
    words_filtering_pretty,
    activity_status_filter,
    LEARNING_LANGUAGES_MARKUP_SIZE,
)


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

router = Router()

VOCABULARY_WORDS_PER_PAGE = 3  # 12
VOCABULARY_WORDS_MARKUP_SIZE = 3
VOCABULARY_TYPES_MARKUP_SIZE = 3
VOCABULARY_ACTIVITY_STATUS_MARKUP_SIZE = 3


async def save_learning_languages_to_state(
    message: Message, state: FSMContext, headers: dict
) -> dict:
    """Makes API request to get leraning languages, saves response data to state data, returns dictionary."""
    url = LEARNING_LANGUAGES_URL + '?no_words'
    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    await state.set_state(User.learning_languages_info)
                    response_data: dict = await response.json()

                    learning_languages_info = {}
                    for language in response_data['results']:
                        learning_languages_info[language['language']['name']] = {
                            'words_count': language['words_count'],
                        }

                    await state.update_data(
                        learning_languages_info=learning_languages_info
                    )

                    return learning_languages_info

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)
                    return None

                case _:
                    await send_error_message(message, state, response)
                    return None


@router.message(F.text == 'Словарь')
async def vocabulary_choose_language(message: Message, state: FSMContext) -> None:
    """Sends user learning languages to choose."""
    await state.set_state(Vocabulary.language_choose)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    # get user learning languages from API if no learning languages info in state_data
    learning_languages_info: dict | None = await save_learning_languages_to_state(
        message, state, headers
    )

    if learning_languages_info is None:
        return None

    if len(learning_languages_info) == 0:
        await vocabulary_choose_language_callback(message, state)
        return None

    if len(learning_languages_info) == 1:
        await vocabulary_choose_language_callback(
            message, state, language_name=list(learning_languages_info.keys())[0]
        )
        return None

    # generate inline keyboard
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.add(
        *[
            InlineKeyboardButton(
                text=f'{language_name} {language_data["words_count"]}',
                callback_data=f'filter_by_language_{language_name}',
            )
            for language_name, language_data in learning_languages_info.items()
        ]
    )
    keyboard_builder.adjust(LEARNING_LANGUAGES_MARKUP_SIZE)
    keyboard_builder.row(
        InlineKeyboardButton(text='Все языки', callback_data='filter_by_language_')
    )
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())

    await message.answer(
        ('Выберите язык, словарь которого хотите открыть: '),
        reply_markup=markup,
    )


def generate_vocabulary_markup(
    state_data: dict, response_data_results: dict
) -> InlineKeyboardMarkup:
    """Returns markup that contains paginated user words."""
    pages_total_amount = state_data.get('pages_total_amount')
    page_num = state_data.get('page_num')

    keyboard_builder = InlineKeyboardBuilder()
    for word_info in response_data_results:
        word_slug = word_info['slug']
        word_text = word_info['text']
        keyboard_builder.add(
            InlineKeyboardButton(
                text=word_text, callback_data=f'word_profile__{word_text}__{word_slug}'
            )
        )

    keyboard_builder.adjust(VOCABULARY_WORDS_MARKUP_SIZE)

    if pages_total_amount and pages_total_amount > 1:
        page_num_button = get_page_num_button(page_num, pages_total_amount)
        keyboard_builder.row(backward_button, page_num_button, forward_button)

    keyboard_builder.row(
        InlineKeyboardButton(text='Вернуться назад', callback_data='cancel')
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())


async def send_vocabulary_answer(
    message: Message, state: FSMContext, response_data: dict, *args, **kwargs
) -> None:
    """Sends user vocabulary data from learning language profile or vocabulary response data."""
    state_data = await state.get_data()

    try:
        results_count = response_data['words']['count']
        results = response_data['words']['results']
        language_name = response_data['language']['name']
        language_name_local = response_data['language']['name_local']

        learning_languages_info = state_data.get('learning_languages_info')[
            language_name
        ]
        cover_id = learning_languages_info['cover_id']

        markup = generate_vocabulary_markup(state_data, results)

        answer_text = state_data.get(
            'answer_text',
            (
                f'Изучаемый язык: {language_name} ({language_name_local}) \n'
                f'Мощность словаря: {results_count} 🔥 \n\n'
            ),
        )

        await message.bot.send_photo(
            message.chat.id,
            photo=cover_id,
            caption=answer_text,
            reply_markup=markup,
        )

    except KeyError:
        results_count = response_data['count']
        results = response_data['results']

        markup = generate_vocabulary_markup(state_data, results)

        answer_text = state_data.get(
            'answer_text', f'Мощность словаря: {results_count} 🔥 \n\n'
        )

        await message.answer(answer_text, reply_markup=markup)


@router.callback_query(F.data.startswith('filter_by_language'))
async def vocabulary_choose_language_callback(
    callback_query: CallbackQuery | Message, state: FSMContext, *args, **kwargs
) -> None:
    """Updates state with user choice from message or callback, makes request to learning language profile or vocabulary API url, sends response data."""
    await state.update_data(previous_state_handler=vocabulary_choose_language)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    if isinstance(callback_query, CallbackQuery):
        message: Message = callback_query.message

        language_name = callback_query.data.split('_')[-1]
        await state.update_data(language_choose=language_name)

        if language_name:
            await callback_query.answer(f'Выбран язык: {language_name}')
        else:
            await callback_query.answer('Выбран язык: Все языки')
    else:
        message: Message = callback_query
        language_name = state_data.get('language_choose')

    await message.answer(
        'Открываю словарь...',
        reply_markup=vocabulary_kb,
    )

    url = (
        LEARNING_LANGUAGES_URL
        + language_name
        + '/'
        + '?'
        + f'limit={VOCABULARY_WORDS_PER_PAGE}'
        if language_name
        else VOCABULARY_URL + '?' + f'limit={VOCABULARY_WORDS_PER_PAGE}'
    )
    await state.update_data(url=url)

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()

                    try:
                        results_count = response_data['words']['count']
                    except KeyError:
                        results_count = response_data['count']

                    # set_pages_total_amount
                    pages_total_amount = math.ceil(
                        results_count / VOCABULARY_WORDS_PER_PAGE
                    )
                    await state.update_data(
                        pages_total_amount=pages_total_amount, page_num=1
                    )

                    try:
                        results = response_data['words']['results']
                        language_name = response_data['language']['name']
                        language_name_local = response_data['language']['name_local']

                        if results_count == 0:
                            answer_text = (
                                f'Изучаемый язык: {language_name} ({language_name_local}) \n'
                                f'Мощность словаря: {results_count} \n\n'
                                f'Выберите пункт меню "Добавить новое слово" или '
                                f'"Добавить несколько новых слов", чтобы пополнить свой словарь ✍️'
                            )
                        else:
                            answer_text = (
                                f'Изучаемый язык: {language_name} ({language_name_local}) \n'
                                f'Мощность словаря: {results_count} 🔥 \n\n'
                            )

                        await state.update_data(answer_text=answer_text)

                        markup = generate_vocabulary_markup(
                            await state.get_data(), results
                        )

                        learning_languages_info: dict = state_data.get(
                            'learning_languages_info'
                        )[language_name]
                        cover_id = learning_languages_info.get('cover_id', None)

                        if cover_id is not None:
                            # send image file with text through file id
                            await message.bot.send_photo(
                                message.chat.id,
                                photo=cover_id,
                                caption=answer_text,
                                reply_markup=markup,
                            )
                        else:
                            cover_url = response_data['cover']
                            # get cover image file from url
                            async with session.get(
                                url=cover_url, headers=headers
                            ) as image_response:
                                cover_image = await image_response.content.read()
                                cover_image_filename = cover_url.split('/')[-1]

                            # send image file with text
                            msg = await message.answer_photo(
                                photo=BufferedInputFile(
                                    file=cover_image, filename=cover_image_filename
                                ),
                                caption=answer_text,
                                reply_markup=markup,
                            )

                            learning_languages_info = state_data.get(
                                'learning_languages_info'
                            )
                            learning_languages_info[language_name][
                                'cover_id'
                            ] = msg.photo[0].file_id

                            await state.update_data(
                                learning_languages_info=learning_languages_info
                            )

                    except KeyError:
                        results = response_data['results']

                        markup = generate_vocabulary_markup(
                            await state.get_data(), results
                        )

                        if results_count == 0:
                            answer_text = (
                                f'Все языки\n'
                                f'Мощность словаря: {results_count} \n\n'
                                f'Выберите пункт меню "Добавить новое слово" или '
                                f'"Добавить несколько новых слов", чтобы пополнить свой словарь ✍️'
                            )
                        else:
                            answer_text = (
                                f'Все языки\n'
                                f'Мощность словаря: {results_count} 🔥 \n\n'
                            )

                        await state.update_data(answer_text=answer_text)

                        # send only text
                        await message.answer(answer_text, reply_markup=markup)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(callback_query.message, state)

                case _:
                    await send_error_message(callback_query.message, state, response)


@router.callback_query(F.data.startswith('forward'))
async def forward_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Sends next vocabulary page, deletes previous."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)
    page_num = state_data.get('page_num')
    if page_num is None:
        page_num = 1
    else:
        page_num += 1

    url = state_data.get('url')
    if '?' in url:
        url += '&' + f'page={page_num}'
    else:
        url += '?' + f'page={page_num}'

    await state.update_data(page_num=page_num)

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()
                    await send_vocabulary_answer(
                        callback_query.message, state, response_data
                    )
                    await callback_query.message.delete()
                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(callback_query.message, state)
                case HTTPStatus.NOT_FOUND:
                    await callback_query.answer('Недоступно')
                case _:
                    await send_error_message(callback_query.message, state, response)


@router.callback_query(F.data.startswith('backward'))
async def backward_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Sends previous vocabulary page, deletes current."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)
    page_num = state_data.get('page_num')
    if page_num is None:
        page_num = 1
    else:
        page_num -= 1

    url = state_data.get('url')
    if '?' in url:
        url += '&' + f'page={page_num}'
    else:
        url += '?' + f'page={page_num}'

    await state.update_data(page_num=page_num)

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()
                    await send_vocabulary_answer(
                        callback_query.message, state, response_data
                    )
                    await callback_query.message.delete()
                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(callback_query.message, state)
                case HTTPStatus.NOT_FOUND:
                    await callback_query.answer('Недоступно')
                case _:
                    await send_error_message(callback_query.message, state, response)


@router.callback_query(F.data.startswith('choose_page'))
async def vocabulary_choose_page_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Sets state that awaits page num from user."""
    await state.set_state(Vocabulary.page_choose)
    await state.update_data(previous_state_handler=vocabulary_choose_language_callback)

    await callback_query.answer('Выбор страницы')

    await callback_query.message.answer(
        'Введите номер нужной страницы.',
        reply_markup=cancel_inline_kb,
    )


@router.message(Vocabulary.page_choose)
async def vocabulary_choose_page_proceed(message: Message, state: FSMContext) -> None:
    """Accepts page num, makes request for chosen page, sends vocabulary answer."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)
    pages_total_amount = state_data.get('pages_total_amount')

    try:
        page_num = int(message.text)
        await state.update_data(page_num=page_num)
    except ValueError:
        await message.answer(
            f'Некорректный номер. Введите номер от 1 до {pages_total_amount}.',
            reply_markup=cancel_inline_kb,
        )
        return None

    if page_num not in range(1, pages_total_amount + 1):
        await message.answer(
            f'Некорректный номер. Введите номер от 1 до {pages_total_amount}.',
            reply_markup=cancel_inline_kb,
        )
        return None

    url = state_data.get('url')
    if '?' in url:
        url += '&' + f'page={page_num}'
    else:
        url += '?' + f'page={page_num}'

    await state.update_data(page_num=page_num)

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()
                    await send_vocabulary_answer(message, state, response_data)
                    await state.set_state(Vocabulary.retrieve)
                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)
                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Поиск')
async def vocabulary_search(message: Message, state: FSMContext) -> None:
    """Sets state that awaits search value from user."""
    await state.set_state(Vocabulary.search)
    await state.update_data(previous_state_handler=vocabulary_choose_language_callback)

    await message.answer(
        'Введите поисковой запрос. Например: yellow.',
        reply_markup=cancel_inline_kb,
    )


@router.message(Vocabulary.search)
async def vocabulary_search_proceed(message: Message, state: FSMContext) -> None:
    """Accepts search value, makes request with passed search value, sends vocabulary answer."""
    search_value = message.text
    await state.update_data(search=search_value)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    url = state_data.get('url')
    if '?' in url:
        url += '&' + f'search={search_value}'
    else:
        url += '?' + f'search={search_value}'

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()

                    await state.update_data(page_num=1)

                    try:
                        results_count = response_data['words']['count']
                    except KeyError:
                        results_count = response_data['count']
                    pages_total_amount = math.ceil(
                        results_count / VOCABULARY_WORDS_PER_PAGE
                    )
                    await state.update_data(
                        pages_total_amount=pages_total_amount, page_num=1
                    )

                    await state.update_data(
                        answer_text=f'Поиск: {search_value} 🔍 \nНайдено слов: {results_count}'
                    )

                    await send_vocabulary_answer(message, state, response_data)
                    await state.set_state(Vocabulary.retrieve)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Сортировка')
async def vocabulary_ordering(message: Message, state: FSMContext) -> None:
    """Sends ordering field options."""
    await state.update_data(previous_state_handler=vocabulary_choose_language_callback)

    await message.answer(
        'Выберите сортировку из предложенных ниже:',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='По тексту', callback_data='order_by__text'
                    ),
                    InlineKeyboardButton(
                        text='По дате добавления', callback_data='order_by__created'
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='По дате последней тренировки',
                        callback_data='order_by__last_exercise_date',
                    ),
                    InlineKeyboardButton(
                        text='По количеству дополнений',
                        callback_data='counters_ordering',
                    ),
                ],
                [InlineKeyboardButton(text='Вернуться назад', callback_data='cancel')],
            ],
        ),
    )


@router.callback_query(F.data.startswith('order_by'))
async def vocabulary_ordering_field_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Updates state with chosen ordering field, sends ordering type options."""
    order_field = callback_query.data.split('__')[-1]
    order_field_pretty = words_ordering_pretty.get(order_field)
    await callback_query.answer(f'Выбрана сортировка: {order_field_pretty}')

    await callback_query.message.answer(
        'Выберите сортировку из предложенных ниже:',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='По убыванию',
                        callback_data=f'order_type__{order_field}__descending',
                    ),
                    InlineKeyboardButton(
                        text='По возрастанию',
                        callback_data=f'order_type__{order_field}__ascending',
                    ),
                ],
                [InlineKeyboardButton(text='Вернуться назад', callback_data='cancel')],
            ],
        ),
    )


@router.callback_query(F.data.startswith('order_type'))
async def vocabulary_ordering_callback_proceed(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Accepts ordering type, makes request with chosen ordering, sends vocabulary answer."""
    order_type = callback_query.data.split('__')[-1]
    order_field = callback_query.data.split('__')[-2]

    order_field_pretty = words_ordering_pretty.get(order_field)
    order_type_pretty = ordering_type_pretty.get(order_type)

    await callback_query.answer(f'Выбран тип сортировки: {order_type_pretty}')

    if order_type == 'descending':
        order_field = f'-{order_field}'

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    url = state_data.get('url')
    if '?' in url:
        url += '&' + f'ordering={order_field}'
    else:
        url += '?' + f'ordering={order_field}'

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()

                    await state.update_data(page_num=1)

                    answer_text = (
                        state_data.get('answer_text')
                        + f'Слова сортированы {order_field_pretty.lower()} ({order_type_pretty.lower()})'
                    )
                    await state.update_data(answer_text=answer_text)

                    await send_vocabulary_answer(
                        callback_query.message, state, response_data
                    )
                    await state.set_state(Vocabulary.retrieve)
                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(callback_query.message, state)
                case _:
                    await send_error_message(callback_query.message, state, response)


@router.callback_query(F.data.startswith('counters_ordering'))
async def vocabulary_counters_ordering_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Sends counters ordering field options."""
    order_field_pretty = words_ordering_pretty.get('counters')
    await callback_query.answer(f'Выбрана сортировка: {order_field_pretty}')

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='По количеству переводов',
                    callback_data='order_by__translations_count',
                ),
                InlineKeyboardButton(
                    text='По количеству примеров',
                    callback_data='order_by__examples_count',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='По количеству определений',
                    callback_data='order_by__definitions_count',
                ),
                InlineKeyboardButton(
                    text='По количеству картинок',
                    callback_data='order_by__image_associations_count',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='По количеству синонимов',
                    callback_data='order_by__synonyms_count',
                ),
                InlineKeyboardButton(
                    text='По количеству антонимов',
                    callback_data='order_by__antonyms_count',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='По количеству форм', callback_data='order_by__forms_count'
                ),
                InlineKeyboardButton(
                    text='По количеству похожих слов',
                    callback_data='order_by__similars_count',
                ),
            ],
            [
                InlineKeyboardButton(
                    text='По количеству тегов', callback_data='order_by__tags_count'
                ),
                InlineKeyboardButton(
                    text='По Количеству типов (частей речи)',
                    callback_data='order_by__types_count',
                ),
            ],
            [
                InlineKeyboardButton(text='Вернуться назад', callback_data='cancel'),
            ],
        ]
    )

    await callback_query.message.answer(
        'Выберите сортировку из предложенных ниже:',
        reply_markup=markup,
    )


@router.message(F.text == 'Фильтры')
async def vocabulary_filtering(message: Message, state: FSMContext) -> None:
    """Sends filtering field options."""
    await state.update_data(previous_state_handler=vocabulary_choose_language_callback)

    await message.answer(
        'Выберите фильтр из предложенных ниже:',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Теги', callback_data='filter_by__tags'),
                    InlineKeyboardButton(
                        text='Типы (части речи)', callback_data='filter_by__types'
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='Первая буква', callback_data='filter_by__first_letter'
                    ),
                    InlineKeyboardButton(
                        text='Последняя буква', callback_data='filter_by__last_letter'
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='Статус активности',
                        callback_data='filter_by__activity_status',
                    ),
                    InlineKeyboardButton(
                        text='Количество дополнений',
                        callback_data='filter_by__counters',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text='Дата добавления', callback_data='filter_by__created'
                    ),
                    InlineKeyboardButton(
                        text='Дата последней тренировки',
                        callback_data='filter_by__last_exercise_date',
                    ),
                ],
                [InlineKeyboardButton(text='Вернуться назад', callback_data='cancel')],
            ],
        ),
    )


@router.callback_query(F.data.startswith('filter_by'))
async def vocabulary_filtering_field_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Accepts chosen filter field, update state that awaits filter value or sends chosen filter options."""
    filter_field = callback_query.data.split('__')[-1]
    filter_field_pretty = words_filtering_pretty.get(filter_field, filter_field)
    await callback_query.answer(f'Выбран фильтр: {filter_field_pretty}')
    await state.update_data(filter_field=filter_field)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)
    filtering = state_data.get('filtering') or {}

    message = callback_query.message

    match filter_field:
        case 'tags':
            filtering[filter_field] = ''
            await state.update_data(filtering=filtering)

            await message.answer(
                'Введите нужные теги чере запятую без пробела между.',
                reply_markup=cancel_inline_kb,
            )

            await state.set_state(Vocabulary.filtering)

        case 'types':
            filtering[filter_field] = ''
            await state.update_data(filtering=filtering)

            # get available types from API
            async with aiohttp.ClientSession() as session:
                api_request_logging(TYPES_URL, headers=headers, method='get')
                async with session.get(url=TYPES_URL, headers=headers) as response:
                    match response.status:
                        case HTTPStatus.OK:
                            response_data: dict = await response.json()
                            types_info = [
                                (
                                    wordtype['name'],
                                    wordtype['slug'],
                                    wordtype['words_count'],
                                )
                                for wordtype in response_data
                            ]
                        case HTTPStatus.UNAUTHORIZED:
                            await send_unauthorized_response(message, state)
                            return None
                        case _:
                            await send_error_message(message, state, response)
                            return None

            keyboard_builder = InlineKeyboardBuilder()
            for type_name, type_slug, type_words_count in types_info:
                keyboard_builder.add(
                    InlineKeyboardButton(
                        text=f'{type_name} ({type_words_count})',
                        callback_data=f'types_filter__{type_slug}',
                    )
                )
            keyboard_builder.adjust(VOCABULARY_TYPES_MARKUP_SIZE)

            keyboard_builder.row(
                InlineKeyboardButton(text='Вернуться назад', callback_data='cancel')
            )

            await callback_query.message.answer(
                'Введите нужные типы (части речи) чере запятую без пробела между или выберите из предложенных ниже:',
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=keyboard_builder.export()
                ),
            )

        case 'first_letter':
            filtering[filter_field] = ''
            await state.update_data(filtering=filtering)

            await message.answer(
                'Введите первую букву.',
                reply_markup=cancel_inline_kb,
            )

            await state.set_state(Vocabulary.filtering)

        case 'last_letter':
            filtering[filter_field] = ''
            await state.update_data(filtering=filtering)

            await message.answer(
                'Введите последнюю букву.',
                reply_markup=cancel_inline_kb,
            )

            await state.set_state(Vocabulary.filtering)

        case 'activity_status':
            filtering[filter_field] = ''
            await state.update_data(filtering=filtering)

            keyboard_builder = InlineKeyboardBuilder()
            for (
                activity_status_short,
                activity_status,
            ) in activity_status_filter.items():
                keyboard_builder.add(
                    InlineKeyboardButton(
                        text=activity_status,
                        callback_data=f'activity_status_filter__{activity_status_short}',
                    )
                )
            keyboard_builder.adjust(VOCABULARY_ACTIVITY_STATUS_MARKUP_SIZE)

            keyboard_builder.row(
                InlineKeyboardButton(text='Вернуться назад', callback_data='cancel')
            )

            await callback_query.message.answer(
                'Выберите статус активности из предложенных ниже:',
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=keyboard_builder.export()
                ),
            )

        case 'counters':
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text='Количество переводов',
                            callback_data='counters_filter__translations_count',
                        ),
                        InlineKeyboardButton(
                            text='Количество примеров',
                            callback_data='counters_filter__examples_count',
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text='Количество определений',
                            callback_data='counters_filter__definitions_count',
                        ),
                        InlineKeyboardButton(
                            text='Количество картинок',
                            callback_data='counters_filter__image_associations_count',
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text='Количество синонимов',
                            callback_data='counters_filter__synonyms_count',
                        ),
                        InlineKeyboardButton(
                            text='Количество антонимов',
                            callback_data='counters_filter__antonyms_count',
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text='Количество форм',
                            callback_data='counters_filter__forms_count',
                        ),
                        InlineKeyboardButton(
                            text='Количество похожих слов',
                            callback_data='counters_filter__similars_count',
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text='Количество тегов',
                            callback_data='counters_filter__tags_count',
                        ),
                        InlineKeyboardButton(
                            text='Количество типов (частей речи)',
                            callback_data='counters_filter__types_count',
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text='Вернуться назад', callback_data='cancel'
                        ),
                    ],
                ]
            )

            await callback_query.message.answer(
                'Выберите фильтр из предложенных ниже:',
                reply_markup=markup,
            )

        case 'created':
            filtering[filter_field] = ''
            await state.update_data(filtering=filtering)

            await message.answer(
                (
                    'Введите дату в формате YYYY-MM-DD (Пример: 2024-10-20). \n\n'
                    'Для фильтрации только по году или месяцу добавления '
                    'введите только год или месяц (номер) соответственно. \n\n'
                    'Укажите через пробел перед датой знак &gt; или &lt; '
                    'для фильтра по значениям больше или меньше переданного соответственно.'
                ),
                reply_markup=cancel_inline_kb,
            )

            await state.set_state(Vocabulary.date_filter_value)

        case 'last_exercise_date':
            filtering[filter_field] = ''
            await state.update_data(filtering=filtering)

            await message.answer(
                (
                    'Введите дату в формате YYYY-MM-DD (Пример: 2024-10-20). \n\n'
                    'Для фильтрации только по году или месяцу последней тренировки '
                    'введите только год или месяц (номером) соответственно. \n\n'
                    'Укажите через пробел перед датой знак &gt; или &lt; '
                    'для фильтра по значениям больше или меньше переданного соответственно.'
                ),
                reply_markup=cancel_inline_kb,
            )

            await state.set_state(Vocabulary.date_filter_value)

        case _:
            raise AssertionError('no filter match')


@router.message(Vocabulary.filtering)
async def vocabulary_filtering_proceed(
    message: Message, state: FSMContext, *args, **kwargs
) -> None:
    """Accepts filter value, makes request with passed filter field, value, send vocabulary answer."""
    filter_value = kwargs.get('filter_value')
    filter_value = message.text if filter_value is None else filter_value

    state_data = await state.get_data()
    filter_field = state_data.get('filter_field')
    filter_field_pretty = words_filtering_pretty.get(filter_field)
    filtering = state_data.get('filtering')
    filtering[filter_field] = filter_value

    await state.update_data(filtering=filtering)

    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    url = state_data.get('url')
    if '?' in url:
        url += '&' + f'{filter_field}={filter_value}'
    else:
        url += '?' + f'{filter_field}={filter_value}'

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()

                    await state.update_data(page_num=1)

                    try:
                        results_count = response_data['words']['count']
                    except KeyError:
                        results_count = response_data['count']
                    pages_total_amount = math.ceil(
                        results_count / VOCABULARY_WORDS_PER_PAGE
                    )
                    await state.update_data(
                        pages_total_amount=pages_total_amount, page_num=1
                    )

                    filter_value = kwargs.get('filter_value_pretty') or filter_value

                    await state.update_data(
                        answer_text=(
                            f'Фильтр: {filter_field_pretty} 👀 \n'
                            f'Значение: {filter_value} \n'
                            f'Найдено слов: {results_count}'
                        )
                    )

                    await send_vocabulary_answer(message, state, response_data)
                    await state.set_state(Vocabulary.retrieve)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.callback_query(F.data.startswith('types_filter'))
async def vocabulary_types_filter_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Calls filtering proceed with chosen types filter option."""
    filter_value = callback_query.data.split('__')[-1]
    await callback_query.answer(f'Выбран тип: {filter_value}')

    await vocabulary_filtering_proceed(
        callback_query.message, state, filter_value=filter_value
    )


@router.callback_query(F.data.startswith('activity_status_filter'))
async def vocabulary_activity_status_filter_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Calls filtering proceed with chosen activity status filter option."""
    filter_value = callback_query.data.split('__')[-1]
    activity_status = activity_status_filter.get(filter_value, filter_value)
    await callback_query.answer(f'Выбран статус: {activity_status}')

    await vocabulary_filtering_proceed(
        callback_query.message,
        state,
        filter_value=filter_value,
        filter_value_pretty=activity_status,
    )


@router.callback_query(F.data.startswith('counters_filter'))
async def vocabulary_counters_filter_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Updates state with chosen counters filter field, sets state that awaits counters filter value."""
    state_data = await state.get_data()
    filter_field = callback_query.data.split('__')[-1]
    filtering = state_data.get('filtering') or {}
    filtering[filter_field] = ''
    await state.update_data(filtering=filtering, filter_field=filter_field)

    filter_value_pretty = words_filtering_pretty.get(filter_field, filter_field)
    await callback_query.answer(f'Выбран фильтр: {filter_value_pretty}')

    await callback_query.message.answer(
        (
            'Введите нужное количество. \n\n'
            'Укажите перед значением через пробел знак &gt; или &lt; '
            'для фильтра по значениям больше или меньше переданного соответственно.'
        ),
        reply_markup=cancel_inline_kb,
    )

    await state.set_state(Vocabulary.counters_filter_value)


@router.message(Vocabulary.counters_filter_value)
async def vocabulary_counters_filter_proceed(
    message: Message, state: FSMContext
) -> None:
    """Accepts counters filter value, calls vocabulary filtering proceed."""
    state_data = await state.get_data()
    filter_field = state_data.get('filter_field')

    # check if __gt or __lt prefix are required
    filter_value = message.text.split(' ')
    if len(filter_value) > 1:
        match filter_value[0]:
            case '>':
                filter_field += '__gt'
                await state.update_data(filter_field=filter_field)
            case '<':
                filter_field += '__lt'
                await state.update_data(filter_field=filter_field)
            case _:
                await message.answer(
                    (
                        'Передан некорректный знак, ожидался &gt; или &lt;, проверьте правильность написания. \n\n '
                        'Введите нужное количество. \n'
                        'Укажите перед значением через пробел знак &gt; или &lt; '
                        'для фильтра по значениям больше или меньше переданного соответственно.'
                    ),
                    reply_markup=cancel_inline_kb,
                )
        filter_value = filter_value[1]
    else:
        filter_value = filter_value[0]

    # check if valid digit was passed
    try:
        filter_value = int(filter_value)
    except ValueError:
        await message.answer(
            (
                'Передано некорректное число, проверьте правильность написания. \n\n '
                'Введите нужное количество. \n'
                'Укажите перед значением через пробел знак &gt; или &lt; '
                'для фильтра по значениям больше или меньше переданного соответственно.'
            ),
            reply_markup=cancel_inline_kb,
        )

    await vocabulary_filtering_proceed(message, state, filter_value=filter_value)


@router.message(Vocabulary.date_filter_value)
async def vocabulary_date_filter_proceed(
    message: Message, state: FSMContext, *args, **kwargs
) -> None:
    """Accepts date filter value, calls vocabulary filtering proceed."""
    state_data = await state.get_data()
    filter_field = state_data.get('filter_field')

    filter_value = message.text.split(' ')
    if len(filter_value) > 1:
        # check if year or month only were passed
        if len(filter_value[1]) == 2:
            filter_field += '__month'
            await state.update_data(filter_field=filter_field)
        elif len(filter_value[1]) == 4:
            filter_field += '__year'
            await state.update_data(filter_field=filter_field)
        else:
            filter_field += '__date'
            await state.update_data(filter_field=filter_field)

        # check if __gt or __lt prefix are required
        match filter_value[0]:
            case '>':
                filter_field += '__gt'
                await state.update_data(filter_field=filter_field)
            case '<':
                filter_field += '__lt'
                await state.update_data(filter_field=filter_field)
            case _:
                await message.answer(
                    (
                        'Передан некорректный знак, ожидался &gt; или &lt;, проверьте правильность написания. \n\n '
                        'Введите нужное количество. \n'
                        'Укажите перед значением через пробел знак &gt; или &lt; '
                        'для фильтра по значениям больше или меньше переданного соответственно.'
                    ),
                    reply_markup=cancel_inline_kb,
                )
        filter_value = filter_value[1]
    else:
        # check if year or month only were passed
        if len(filter_value[0]) == 2:
            filter_field += '__month'
            await state.update_data(filter_field=filter_field)
        elif len(filter_value[0]) == 4:
            filter_field += '__year'
            await state.update_data(filter_field=filter_field)

        filter_value = filter_value[0]

    await vocabulary_filtering_proceed(message, state, filter_value=filter_value)
