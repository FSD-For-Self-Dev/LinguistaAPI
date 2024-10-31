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
    return_button,
)
from keyboards.vocabulary import vocabulary_kb
from keyboards.generators import generate_vocabulary_markup
from states.vocabulary import Vocabulary

from ..urls import VOCABULARY_URL, LEARNING_LANGUAGES_URL
from ..utils import (
    send_error_message,
    send_unauthorized_response,
    send_vocabulary_answer,
    send_vocabulary_answer_from_state_data,
    save_learning_languages_to_state,
    save_types_info_to_state,
    save_paginated_words_to_state,
    api_request_logging,
    get_authentication_headers,
    choose_page,
    get_next_page,
    get_previous_page,
    filter_by_date,
    filter_by_counter,
)
from .constants import (
    words_ordering_pretty,
    ordering_type_pretty,
    words_filtering_pretty,
    activity_status_filter,
    LEARNING_LANGUAGES_MARKUP_SIZE,
    VOCABULARY_WORDS_PER_PAGE,
    VOCABULARY_TYPES_MARKUP_SIZE,
    VOCABULARY_ACTIVITY_STATUS_MARKUP_SIZE,
)


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == 'Словарь')
async def vocabulary_choose_language(
    message: Message | CallbackQuery, state: FSMContext
) -> None:
    """Sends user learning languages to choose."""
    await state.set_state(Vocabulary.language_choose)
    await state.update_data(vocabulary_send_request=True)

    if isinstance(message, CallbackQuery):
        message = message.message

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)

    # get user learning languages from API if no learning languages info in state_data
    async with aiohttp.ClientSession() as session:
        learning_languages_info: dict[
            dict
        ] | None = await save_learning_languages_to_state(
            message, state, session, headers
        )

    if learning_languages_info is None:
        return None

    if len(learning_languages_info) == 0:
        await vocabulary_choose_language_callback(message, state)
        return None

    if len(learning_languages_info) == 1:
        await state.update_data(language_choose=list(learning_languages_info)[0])
        await vocabulary_choose_language_callback(message, state)
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


@router.callback_query(F.data.startswith('filter_by_language'))
async def vocabulary_choose_language_callback(
    callback_query: CallbackQuery | Message, state: FSMContext, *args, **kwargs
) -> None:
    """Updates state with user choice from message or callback, makes request to learning language profile or vocabulary API url, sends response data."""
    await state.update_data(previous_state_handler=vocabulary_choose_language)
    await state.set_state(Vocabulary.list_retrieve)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)

    if isinstance(callback_query, CallbackQuery):
        message: Message = callback_query.message
        language_name = callback_query.data.split('_')[-1]
        await state.update_data(language_choose=language_name)
        state_data = await state.get_data()
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

    vocabulary_send_request = state_data.get('vocabulary_send_request')
    vocabulary_paginated = state_data.get('vocabulary_paginated')

    if not vocabulary_send_request and language_name in vocabulary_paginated:
        await send_vocabulary_answer_from_state_data(message, state)
        return None

    url = (
        LEARNING_LANGUAGES_URL + f'{language_name}/'
        if language_name
        else VOCABULARY_URL
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

                    # set pages_total_amount value
                    pages_total_amount = math.ceil(
                        results_count / VOCABULARY_WORDS_PER_PAGE
                    )
                    await state.update_data(
                        pages_total_amount=pages_total_amount,
                        page_num=1,
                    )

                    try:
                        # getting words from learning language profile response
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

                        await state.update_data(vocabulary_answer_text=answer_text)

                        # saving words to state by pages
                        vocabulary_paginated = await save_paginated_words_to_state(
                            state,
                            response_data['words'],
                            results_count,
                            language_name=language_name,
                        )
                        markup = await generate_vocabulary_markup(
                            state, vocabulary_paginated
                        )

                        # get learning language cover image
                        learning_languages_info: dict = state_data.get(
                            'learning_languages_info'
                        )
                        cover_id = learning_languages_info[language_name].get(
                            'cover_id', None
                        )

                        if cover_id is not None:
                            # send cover image file through file id
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

                            # send cover image file with caption
                            msg = await message.answer_photo(
                                photo=BufferedInputFile(
                                    file=cover_image, filename=cover_image_filename
                                ),
                                caption=answer_text,
                                reply_markup=markup,
                            )

                            # save cover id to state
                            learning_languages_info[language_name][
                                'cover_id'
                            ] = msg.photo[-1].file_id

                            await state.update_data(
                                learning_languages_info=learning_languages_info
                            )

                    except KeyError:
                        # getting words from vocabulary response
                        vocabulary_paginated = await save_paginated_words_to_state(
                            state,
                            response_data,
                            results_count,
                            language_name=language_name,
                        )
                        markup = await generate_vocabulary_markup(
                            state, vocabulary_paginated
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

                        await state.update_data(vocabulary_answer_text=answer_text)

                        await message.answer(
                            answer_text,
                            reply_markup=markup,
                        )

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.callback_query(F.data.startswith('forward__vocabulary'))
async def vocabulary_forward_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Sends next vocabulary page, deletes previous."""
    state_data = await state.get_data()
    language_choose = state_data.get('language_choose')
    language_name = callback_query.data.split('__')[-1]
    state_type = await state.get_state()

    if language_name != language_choose and state_type == Vocabulary.list_retrieve:
        words_count = state_data.get('vocabulary_words_count')[language_name]
        name_local = state_data.get('learning_languages_info')[language_name][
            'name_local'
        ]
        answer_text = (
            f'Изучаемый язык: {language_name} ({name_local}) \n'
            f'Мощность словаря: {words_count} 🔥 \n\n'
        )
        await state.update_data(
            vocabulary_answer_text=answer_text,
            language_choose=language_name,
        )

    await get_next_page(state)
    await send_vocabulary_answer_from_state_data(callback_query.message, state)
    await callback_query.message.delete()


@router.callback_query(F.data.startswith('backward__vocabulary'))
async def vocabulary_backward_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Sends previous vocabulary page, deletes current."""
    state_data = await state.get_data()
    language_choose = state_data.get('language_choose')
    language_name = callback_query.data.split('__')[-1]
    state_type = await state.get_state()

    if language_name != language_choose and state_type == Vocabulary.list_retrieve:
        words_count = state_data.get('vocabulary_words_count')[language_name]
        name_local = state_data.get('learning_languages_info')[language_name][
            'name_local'
        ]
        answer_text = (
            f'Изучаемый язык: {language_name} ({name_local}) \n'
            f'Мощность словаря: {words_count} 🔥 \n\n'
        )
        await state.update_data(
            vocabulary_answer_text=answer_text,
            language_choose=language_name,
        )

    await get_previous_page(state)
    await send_vocabulary_answer_from_state_data(callback_query.message, state)
    await callback_query.message.delete()


@router.callback_query(F.data.startswith('choose_page__vocabulary'))
async def vocabulary_choose_page_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Sets state that awaits page num from user."""
    language_name = callback_query.data.split('__')[-1]
    await state.update_data(
        previous_state_handler=vocabulary_choose_language_callback,
        language_callback=language_name,
    )

    await callback_query.answer('Выбор страницы')
    await state.set_state(Vocabulary.page_choose)

    await callback_query.message.answer(
        'Введите номер нужной страницы.',
        reply_markup=cancel_inline_kb,
    )


@router.message(Vocabulary.page_choose)
async def vocabulary_choose_page_proceed(message: Message, state: FSMContext) -> None:
    """Accepts page num, makes request for chosen page, sends vocabulary answer."""
    state_data = await state.get_data()
    language_choose = state_data.get('language_choose')
    language_name = state_data.get('language_callback')

    if language_name != language_choose:
        words_count = state_data.get('vocabulary_words_count')[language_name]
        name_local = state_data.get('learning_languages_info')[language_name][
            'name_local'
        ]
        answer_text = (
            f'Изучаемый язык: {language_name} ({name_local}) \n'
            f'Мощность словаря: {words_count} 🔥 \n\n'
        )
        await state.update_data(
            vocabulary_answer_text=answer_text,
            language_choose=language_name,
        )

    await choose_page(message, state)
    await send_vocabulary_answer_from_state_data(message, state)
    await message.delete()


@router.message(F.text == 'Поиск', Vocabulary.list_retrieve)
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
    headers = await get_authentication_headers(token=token)

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

                    try:
                        results_count = response_data['words']['count']
                    except KeyError:
                        results_count = response_data['count']

                    pages_total_amount = math.ceil(
                        results_count / VOCABULARY_WORDS_PER_PAGE
                    )
                    await state.update_data(
                        pages_total_amount=pages_total_amount,
                        page_num=1,
                        vocabulary_answer_text=f'Поиск: {search_value} 🔍 \nНайдено слов: {results_count}',
                    )

                    await send_vocabulary_answer(message, state, response_data)
                    await state.set_state(Vocabulary.list_retrieve)
                    await state.update_data(vocabulary_send_request=True)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Сортировка', Vocabulary.list_retrieve)
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
                [return_button],
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
                [return_button],
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
    headers = await get_authentication_headers(token=token)

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

                    try:
                        results_count = response_data['words']['count']
                        language_name = response_data['language']['name']
                        language_name_local = response_data['language']['name_local']
                        answer_text = (
                            f'Изучаемый язык: {language_name} ({language_name_local}) \n'
                            f'Мощность словаря: {results_count} 🔥 \n\n'
                        )
                    except KeyError:
                        results_count = response_data['count']
                        answer_text = f'Мощность словаря: {results_count} 🔥 \n\n'

                    answer_text += (
                        f'Все языки \n'
                        f'Слова сортированы {order_field_pretty.lower()} ({order_type_pretty.lower()})'
                    )
                    pages_total_amount = math.ceil(
                        results_count / VOCABULARY_WORDS_PER_PAGE
                    )
                    await state.update_data(
                        pages_total_amount=pages_total_amount,
                        page_num=1,
                        vocabulary_answer_text=answer_text,
                    )

                    await send_vocabulary_answer(
                        callback_query.message, state, response_data
                    )
                    await state.set_state(Vocabulary.list_retrieve)
                    await state.update_data(vocabulary_send_request=True)

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
                return_button,
            ],
        ]
    )

    await callback_query.message.answer(
        'Выберите сортировку из предложенных ниже:',
        reply_markup=markup,
    )


@router.message(F.text == 'Фильтры', Vocabulary.list_retrieve)
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
                [return_button],
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
    headers = await get_authentication_headers(token=token)
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
                types_available: list[dict] = await save_types_info_to_state(
                    message, state, session, headers
                )

            keyboard_builder = InlineKeyboardBuilder()
            for type_index, type_info in enumerate(types_available):
                keyboard_builder.add(
                    InlineKeyboardButton(
                        text=f'{type_info["name"]} ({type_info["words_count"]})',
                        callback_data=f'types_filter__{type_index}',
                    )
                )
            keyboard_builder.adjust(VOCABULARY_TYPES_MARKUP_SIZE)

            keyboard_builder.row(return_button)

            await callback_query.message.answer(
                'Введите нужные типы (части речи) через запятую без пробела между или выберите из предложенных ниже:',
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

            keyboard_builder.row(return_button)

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
                    [return_button],
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
    headers = await get_authentication_headers(token=token)

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

                    try:
                        results_count = response_data['words']['count']
                    except KeyError:
                        results_count = response_data['count']

                    filter_value = kwargs.get('filter_value_pretty') or filter_value
                    pages_total_amount = math.ceil(
                        results_count / VOCABULARY_WORDS_PER_PAGE
                    )
                    await state.update_data(
                        pages_total_amount=pages_total_amount,
                        page_num=1,
                        vocabulary_answer_text=(
                            f'Фильтр: {filter_field_pretty} 👀 \n'
                            f'Значение: {filter_value} \n'
                            f'Найдено слов: {results_count}'
                        ),
                    )

                    await send_vocabulary_answer(message, state, response_data)
                    await state.set_state(Vocabulary.list_retrieve)
                    await state.update_data(vocabulary_send_request=True)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.callback_query(F.data.startswith('types_filter'))
async def vocabulary_types_filter_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Calls filtering proceed with chosen types filter option."""
    state_data = await state.get_data()
    types_available = state_data.get('types_available')
    type_index = int(callback_query.data.split('__')[-1])
    type_info = types_available[type_index]
    await callback_query.answer(f'Выбран тип: {type_info["name"]}')
    await vocabulary_filtering_proceed(
        callback_query.message, state, filter_value=type_info['slug']
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
    await filter_by_counter(message, state, filter_handler=vocabulary_filtering_proceed)


@router.message(Vocabulary.date_filter_value)
async def vocabulary_date_filter_proceed(
    message: Message, state: FSMContext, *args, **kwargs
) -> None:
    """Accepts date filter value, calls vocabulary filtering proceed."""
    await filter_by_date(message, state, filter_handler=vocabulary_filtering_proceed)


@router.message(F.text == 'Избранное', Vocabulary.list_retrieve)
async def vocabulary_favorites(message: Message, state: FSMContext) -> None:
    """Sends user favorite words from API response data."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)

    url = VOCABULARY_URL + 'favorites/'

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()
                    results_count = response_data['count']

                    pages_total_amount = math.ceil(
                        results_count / VOCABULARY_WORDS_PER_PAGE
                    )
                    await state.update_data(
                        pages_total_amount=pages_total_amount,
                        page_num=1,
                        vocabulary_answer_text=f'⭐️Избранные слова: {results_count}',
                    )

                    await send_vocabulary_answer(message, state, response_data)
                    await state.set_state(Vocabulary.list_retrieve)
                    await state.update_data(vocabulary_send_request=True)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)
