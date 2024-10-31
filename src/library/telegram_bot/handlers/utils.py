"""Some useful utils."""

import os
import logging
import math
import itertools
from http import HTTPStatus
from typing import Callable

import aiohttp
import aiohttp.client_reqrep
from aiogram.types import (
    Message,
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

from keyboards.core import (
    initial_kb,
    return_kb,
    cancel_button,
    cancel_inline_kb,
    nested_object_already_exist_inlin_kb,
)
from keyboards.user_profile import profile_kb
from keyboards.generators import (
    generate_vocabulary_markup,
    generate_word_profile_markup,
    generate_collections_markup,
)
from states.core import User

from .urls import (
    LEARNING_LANGUAGES_URL,
    TYPES_URL,
    NATIVE_LANGUAGES_URL,
)
from .vocabulary.constants import (
    fields_pretty,
    additions_pretty,
    VOCABULARY_WORDS_PER_PAGE,
    COLLECTIONS_PER_PAGE,
)


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def get_authentication_headers(
    token_auth=True, content_type='json', *args, **kwargs
) -> dict | None:
    """Returns dict of request headers."""
    if token_auth:
        token = kwargs.get('token', '')
        if token:
            match content_type:
                case 'json':
                    return {
                        'Authorization': f'Token {token}',
                        'Content-Type': 'application/json',
                    }
                case _:
                    return {'Authorization': f'Token {token}'}
    return None


async def cancel(message: Message, state: FSMContext) -> None:
    """Clears state and returns to initial state"""
    await state.clear()
    await message.answer(
        'Операция отменена. Зарегистрируйтесь или войдите для продолжения.',
        reply_markup=initial_kb,
    )


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def paginate_values_list(lst, n) -> dict:
    """Returns dictionary with pages numbers, pages values."""
    lst_chunks = list(chunks(lst, n))
    return {
        page_num + 1: page_values for page_num, page_values in enumerate(lst_chunks)
    }


def api_request_logging(url, data=None, headers=None, method='get') -> None:
    logger.debug(
        f'Sending request to API url: {url} (method: {method}, headers: {headers}, data: {data})'
    )


def generate_validation_errors_answer_text(
    invalid_fields_data: dict, fields_pretty, answer_text: str = ''
):
    """Returns validation errors response answer text."""
    try:
        for invalid_field, messages in invalid_fields_data.items():
            answer_text += f'{fields_pretty[invalid_field][0]}: \n'
            for detail_message in messages:
                if isinstance(detail_message, str):
                    answer_text += f'\t- {detail_message} \n'
                else:
                    for key, value in detail_message.items():
                        value_str = '\n\t\t\t\t-- '.join(value)
                        key_str = fields_pretty[key][0]
                        answer_text += f'\t- {key_str}: \n\t\t\t\t-- {value_str} \n'
            answer_text += '\n'

        answer_text += 'Пожалуйста, исправьте ошибки и повторите попытку.'

    except KeyError:
        detail_messages = list(
            itertools.chain.from_iterable(invalid_fields_data.values())
        )
        answer_text = '\n'.join(detail_messages)

    except AttributeError:
        answer_text = '\n'.join(invalid_fields_data)

    return answer_text


def generate_word_profile_answer_text(state_data: dict, response_data: dict) -> str:
    """Returns word profile text info."""
    language_name = response_data['language']
    activity_status = response_data['activity_status']
    text = response_data['text']

    answer_text = (
        f'Язык: {language_name} \n'
        f'Статус активности: {activity_status} \n\n'
        f'<b>{text}</b> \n\n'
    )

    word_types = response_data['types']
    if word_types:
        types_string = ', '.join(word_types)
    else:
        types_string = '<i>Не указаны</i>'
    answer_text += f'Типы (части речи): {types_string} \n'

    form_groups = response_data['form_groups']
    if form_groups:
        form_groups_string = ', '.join(
            map(lambda form_group: form_group['name'], form_groups)
        )
    else:
        form_groups_string = '<i>Не указаны</i>'
    answer_text += f'Группы форм (форма): {form_groups_string} \n'

    tags = response_data['tags']
    if tags:
        tags_string = ', '.join(map(lambda tag: tag['name'], tags))
    else:
        tags_string = '<i>Не указаны</i>'
    answer_text += f'Теги: {tags_string} \n'

    note = response_data['note']
    if note:
        answer_text += f'\nЗаметка: {note} \n'

    favorite = response_data['favorite']
    if favorite:
        answer_text += '\n⭐️ <i>Слово в избранном</i> \n'

    is_problematic = response_data['is_problematic']
    if is_problematic:
        answer_text += '\n⚠️ <i>Проблемное слово</i> \n'

    answer_text += '\n'

    created = response_data['created']
    answer_text += f'<i>Добавлено: {created}</i> \n'

    last_exercise_date = response_data['last_exercise_date']
    if last_exercise_date:
        answer_text += (
            f'<i>Последняя тренировка с этим словом: {last_exercise_date}</i>'
        )
    else:
        answer_text += '<i>Последняя тренировка с этим словом: - </i>'

    return answer_text


def generate_word_create_request_data(
    word_data: dict, word_text: str | None = None, word_language: str | None = None
) -> dict:
    """Returns word create request data generated from state data."""
    word_language = (
        word_data.get('language') if word_language is None else word_language
    )
    word_text = word_data.get('text') if word_text is None else word_text

    request_data = {
        'language': word_language,
        'text': word_text,
        'note': word_data.get('note') if word_data.get('note') else '',
        'types': [word_type.capitalize() for word_type in word_data.get('types')],
        'form_groups': [
            {
                'language': word_language,
                'name': form_group,
            }
            for form_group in word_data.get('form_groups')
        ],
        'tags': [
            {
                'name': tag,
            }
            for tag in word_data.get('tags')
        ],
        'collections': [
            {
                'title': collection,
            }
            for collection in word_data.get('collections')
        ],
        'translations': [],
        'examples': [
            {
                'language': word_language,
                'text': example,
            }
            for example in word_data.get('examples')
        ],
        'definitions': [
            {
                'language': word_language,
                'text': definition,
            }
            for definition in word_data.get('definitions')
        ],
        'image_associations': [
            {
                'image': image_b64,
            }
            for _, image_b64 in word_data.get('image_associations')
        ],
        'synonyms': [
            {
                'from_word': {
                    'language': word_language,
                    'text': synonym,
                },
            }
            for synonym in word_data.get('synonyms')
        ],
        'antonyms': [
            {
                'from_word': {
                    'language': word_language,
                    'text': antonym,
                },
            }
            for antonym in word_data.get('antonyms')
        ],
        'forms': [
            {
                'from_word': {
                    'language': word_language,
                    'text': form,
                },
            }
            for form in word_data.get('forms')
        ],
        'similars': [
            {
                'from_word': {
                    'language': word_language,
                    'text': similar,
                },
            }
            for similar in word_data.get('similars')
        ],
    }

    for language_name, translation in word_data.get('translations'):
        if language_name:
            request_data['translations'].append(
                {
                    'language': language_name,
                    'text': translation,
                }
            )
        else:
            request_data['translations'].append(
                {
                    'text': translation,
                }
            )

    return request_data


async def get_next_page(state: FSMContext) -> None:
    """Updates state data with next page number."""
    state_data = await state.get_data()
    page_num = state_data.get('page_num')
    pages_total_amount = state_data.get('pages_total_amount')

    if page_num is None or page_num == pages_total_amount:
        page_num = 1
    else:
        page_num += 1

    await state.update_data(page_num=page_num)


async def get_previous_page(state: FSMContext) -> None:
    """Updates state data with previous page number."""
    state_data = await state.get_data()
    page_num = state_data.get('page_num')
    pages_total_amount = state_data.get('pages_total_amount')

    if page_num is None:
        page_num = 1
    elif page_num == 1:
        page_num = pages_total_amount
    else:
        page_num -= 1

    await state.update_data(page_num=page_num)


async def choose_page(message: Message, state: FSMContext) -> None:
    """Validates passed page number, updates state data with passed page number."""
    state_data = await state.get_data()
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

    await state.update_data(page_num=page_num)


async def filter_by_date(
    message: Message, state: FSMContext, filter_handler: Callable
) -> None:
    """Updates state data with valid date filter value."""
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

    await filter_handler(message, state, filter_value=filter_value)


async def filter_by_counter(
    message: Message, state: FSMContext, filter_handler: Callable
) -> None:
    """Updates state data with valid counter filter value."""
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

    await filter_handler(message, state, filter_value=filter_value)


# --- Savers ---


async def save_paginated_words_to_state(
    state: FSMContext, words: list[dict], words_count: int, language_name: str = ''
) -> dict:
    """Updates state data with paginated words list."""
    state_data = await state.get_data()
    vocabulary_paginated = (
        state_data.get('vocabulary_paginated')
        if state_data.get('vocabulary_paginated')
        else {}
    )
    vocabulary_words_count = (
        state_data.get('vocabulary_words_count')
        if state_data.get('vocabulary_words_count')
        else {}
    )
    vocabulary_words_list = (
        state_data.get('vocabulary_words_list')
        if state_data.get('vocabulary_words_list')
        else {}
    )
    words_info_list = [
        {'text': word_info['text'], 'slug': word_info['slug']} for word_info in words
    ]
    words_paginated = paginate_values_list(words_info_list, VOCABULARY_WORDS_PER_PAGE)

    try:
        vocabulary_paginated[language_name] = words_paginated
        vocabulary_words_count[language_name] = words_count
        vocabulary_words_list[language_name] = words_info_list
    except TypeError:
        vocabulary_paginated = {language_name: words_paginated}
        vocabulary_words_count = {language_name: words_count}
        vocabulary_words_list = {language_name: words_info_list}

    await state.update_data(
        vocabulary_paginated=vocabulary_paginated,
        vocabulary_words_list=vocabulary_words_list,
        vocabulary_words_count=vocabulary_words_count,
        vocabulary_send_request=False,
    )
    return words_paginated


async def save_paginated_collections_to_state(
    state: FSMContext,
    collections: list[dict],
    collections_count: int,
    collections_send_request: bool = False,
) -> dict:
    """Updates state data with paginated collections list."""
    collections_info_list = [
        {'title': collection_info['title'], 'slug': collection_info['slug']}
        for collection_info in collections
    ]
    collections_paginated = paginate_values_list(
        collections_info_list, COLLECTIONS_PER_PAGE
    )
    await state.update_data(
        collections_paginated=collections_paginated,
        collections_count=collections_count,
        collections_list=collections_info_list,
        collections_send_request=collections_send_request,
    )
    return collections_paginated


async def save_learning_languages_to_state(
    message: Message, state: FSMContext, session: aiohttp.ClientSession, headers: dict
) -> dict:
    """Makes API request to get leraning languages, saves response data to state data, returns dictionary."""
    url = LEARNING_LANGUAGES_URL + '?no_words'
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
                        'name_local': language['language']['name_local'],
                        'isocode': language['language']['isocode'],
                    }

                await state.update_data(learning_languages_info=learning_languages_info)

                return learning_languages_info

            case HTTPStatus.UNAUTHORIZED:
                await send_unauthorized_response(message, state)
                return None

            case _:
                await send_error_message(message, state, response)
                return None


async def save_types_info_to_state(
    message: Message, state: FSMContext, session: aiohttp.ClientSession, headers: dict
) -> None:
    """Makes API request to user native languages endpoint, saves response data to state."""
    url = TYPES_URL
    api_request_logging(url, headers=headers, method='get')
    async with session.get(url=url, headers=headers) as response:
        match response.status:
            case HTTPStatus.OK:
                response_data: dict = await response.json()
                types_available = [
                    {
                        'name': word_type['name'],
                        'slug': word_type['slug'],
                        'words_count': word_type['words_count'],
                    }
                    for word_type in response_data
                ]
                await state.update_data(types_available=types_available)
                return types_available
            case HTTPStatus.UNAUTHORIZED:
                await send_unauthorized_response(message, state)
                return None
            case _:
                await send_error_message(message, state, response)
                return None


async def save_native_languages_to_state(
    message: Message, state: FSMContext, session: aiohttp.ClientSession, headers: dict
) -> None:
    """Makes API request to types endpoint, saves response data to state."""
    url = NATIVE_LANGUAGES_URL
    api_request_logging(url, headers=headers, method='get')
    async with session.get(url=url, headers=headers) as response:
        match response.status:
            case HTTPStatus.OK:
                response_data: dict = await response.json()
                native_languages_info = [
                    language['language']['name']
                    for language in response_data['results']
                ]
                await state.update_data(native_languages_info=native_languages_info)
                try:
                    await state.update_data(
                        translations_language=native_languages_info[-1]
                    )
                except IndexError:
                    await message.answer(
                        'Подсказка: укажите родные языки в своем профиле, чтобы добавлять переводы к словам.'
                    )
                return native_languages_info
            case HTTPStatus.UNAUTHORIZED:
                await send_unauthorized_response(message, state)
                return None
            case _:
                await send_error_message(message, state, response)
                return None


# --- Senders ---


async def send_error_message(
    message: Message, state: FSMContext, response: aiohttp.client_reqrep.ClientResponse
) -> None:
    """Sends error message when some unexpected error occured."""
    await state.clear()
    response_data = await response.json()
    await message.answer(
        f'Кажется, что-то пошло не так. Код ответа: {response.status} 👾',
        reply_markup=return_kb,
    )
    logger.debug(
        f'During login API returned {response.status} status response: {response_data}'
    )


async def send_unauthorized_response(message: Message, state: FSMContext) -> None:
    """Sends unauthorized error message."""
    await state.clear()
    await message.answer(
        'Зарегистрируйтесь или войдите для продолжения.',
        reply_markup=initial_kb,
    )


async def send_validation_errors(
    message: Message, state: FSMContext, response: aiohttp.client_reqrep.ClientResponse
) -> None:
    """Sends validation errors messages."""
    response_data: dict = await response.json()
    all_fields_pretty = fields_pretty | additions_pretty

    answer_text = generate_validation_errors_answer_text(
        response_data,
        all_fields_pretty,
        answer_text='🚫 Присутствуют ошибки в переданных данных: \n\n',
    )

    await message.answer(answer_text)


async def send_conflicts_errors(
    message: Message, state: FSMContext, response: aiohttp.client_reqrep.ClientResponse
) -> None:
    """Sends conflicts errors messages."""
    response_data: dict = await response.json()
    try:
        match response_data['exception_code']:
            case 'amount_limit_exceeded':
                detail_message = response_data.get('detail')
                amount_limit = response_data.get('amount_limit')
                detail_message += f' ({amount_limit})'
                await message.answer(detail_message)

            case (
                'word_already_exist'
                | 'synonym_word_already_exist'
                | 'antonym_word_already_exist'
                | 'form_word_already_exist'
                | 'similar_word_already_exist'
            ):
                detail_message = response_data.get('detail')
                existing_word = response_data.get('existing_object')
                new_word_data = response_data.get('new_object')

                existing_word_note = (
                    existing_word['note']
                    if existing_word['note']
                    else '<i>Не указана</i>'
                )
                existing_word_types_str = (
                    ', '.join(existing_word['types'])
                    if existing_word['types']
                    else '<i>Не указаны</i>'
                )
                existing_word_form_groups_str = (
                    ', '.join(
                        [
                            form_group['name']
                            for form_group in existing_word['form_groups']
                        ]
                    )
                    if existing_word['form_groups']
                    else '<i>Не указаны</i>'
                )
                existing_word_tags_str = (
                    ', '.join([tag['name'] for tag in existing_word['tags']])
                    if existing_word['tags']
                    else '<i>Не указаны</i>'
                )
                existing_word_translations = existing_word['translations_count']
                existing_word_examples = existing_word['examples_count']
                existing_word_definitions = existing_word['definitions_count']
                existing_word_image_associations = existing_word['images_count']
                existing_word_collections = existing_word['collections_count']
                detail_message += (
                    f'\n\n<b>{new_word_data["text"]}</b>\n\n'
                    f'📖Профиль слова из вашего словаря:\n'
                    f'Язык: {existing_word["language"]}\n'
                    f'Слово: <b>{existing_word["text"]}</b>\n'
                    f'Заметка: {existing_word_note}\n'
                    f'Группы форм (форма): {existing_word_types_str}\n'
                    f'Типы (части речи): {existing_word_form_groups_str}\n'
                    f'Теги: {existing_word_tags_str}\n\n'
                    f'Переводы: {existing_word_translations}\n'
                    f'Примеры: {existing_word_examples}\n'
                    f'Определения: {existing_word_definitions}\n'
                    f'Картинки-ассоциации: {existing_word_image_associations}\n'
                )

                if response_data['exception_code'] == 'word_already_exist':
                    existing_word_synonyms = existing_word['synonyms_count']
                    existing_word_antonyms = existing_word['antonyms_count']
                    existing_word_forms = existing_word['forms_count']
                    existing_word_similars = existing_word['similars_count']
                    detail_message += (
                        f'Синонимы: {existing_word_synonyms}\n'
                        f'Антонимы: {existing_word_antonyms}\n'
                        f'Формы: {existing_word_forms}\n'
                        f'Похожие слова: {existing_word_similars}\n'
                        f'Коллекции: {existing_word_collections}\n'
                    )

                    await state.update_data(
                        existing_word_id=existing_word['id'],
                        new_word_text=new_word_data['text'],
                        existing_word_data=existing_word,
                        conflict_object_index=response_data.get(
                            'conflict_object_index', None
                        ),
                    )

                    update_callback = 'word_create_existing_word__update'
                    get_callback = 'word_create_existing_word__get'

                else:
                    detail_message += f'Коллекции: {existing_word_collections}\n'

                    nested_field_name = (
                        response_data['exception_code'].split('_')[0] + 's'
                    )

                    await state.update_data(
                        existing_nested_object_id=existing_word['id'],
                        conflict_nested_field=nested_field_name,
                        conflict_object_index=response_data.get(
                            'conflict_object_index', None
                        ),
                        conflict_field=response_data.get('conflict_field', ''),
                        new_nested_object_data=new_word_data,
                        existing_nested_object_data=existing_word,
                    )

                    update_callback = 'word_create_existing_nested__from_word__update'
                    get_callback = 'word_create_existing_nested__from_word__get'

                await message.answer(
                    detail_message,
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text='Обновить',
                                    callback_data=update_callback,
                                ),
                            ],
                            [
                                InlineKeyboardButton(
                                    text='Взять из словаря',
                                    callback_data=get_callback,
                                ),
                            ],
                            [
                                cancel_button,
                            ],
                        ]
                    ),
                )

            case 'wordtranslation_already_exist':
                detail_message = response_data.get('detail')
                existing_object = response_data.get('existing_object')
                new_object_data = response_data.get('new_object')

                detail_message += (
                    f'\n\n<b>{new_object_data["text"]}</b>\n\n'
                    f'📖Перевод из вашего словаря:\n'
                    f'Язык: {existing_object["language"]}\n'
                    f'Перевод: <b>{existing_object["text"]}</b>\n'
                )

                await state.update_data(
                    existing_nested_object_id=existing_object['id'],
                    conflict_nested_field='translations',
                    conflict_object_index=response_data.get(
                        'conflict_object_index', None
                    ),
                    conflict_field=response_data.get('conflict_field', ''),
                    new_nested_object_data=new_object_data,
                    existing_nested_object_data=existing_object,
                )

                await message.answer(
                    detail_message,
                    reply_markup=nested_object_already_exist_inlin_kb,
                )

            case 'usageexample_already_exist':
                detail_message = response_data.get('detail')
                existing_object = response_data.get('existing_object')
                new_object_data = response_data.get('new_object')

                detail_message += (
                    f'\n\n<b>{new_object_data["text"]}</b>\n\n'
                    f'📖Пример из вашего словаря:\n'
                    f'Язык: {existing_object["language"]}\n'
                    f'Пример: <b>{existing_object["text"]}</b>\n'
                    f'Перевод примера: {existing_object["translation"]}\n'
                )

                await state.update_data(
                    existing_nested_object_id=existing_object['id'],
                    conflict_nested_field='examples',
                    conflict_object_index=response_data.get(
                        'conflict_object_index', None
                    ),
                    conflict_field=response_data.get('conflict_field', ''),
                    new_nested_object_data=new_object_data,
                    existing_nested_object_data=existing_object,
                )

                await message.answer(
                    detail_message,
                    reply_markup=nested_object_already_exist_inlin_kb,
                )

            case 'definition_already_exist':
                detail_message = response_data.get('detail')
                existing_object = response_data.get('existing_object')
                new_object_data = response_data.get('new_object')

                detail_message += (
                    f'\n\n<b>{new_object_data["text"]}</b>\n\n'
                    f'📖Определение из вашего словаря:\n'
                    f'Язык: {existing_object["language"]}\n'
                    f'Определение: <b>{existing_object["text"]}</b>\n'
                    f'Перевод определения: {existing_object["translation"]}\n'
                )

                await state.update_data(
                    existing_nested_object_id=existing_object['id'],
                    conflict_nested_field='definitions',
                    conflict_object_index=response_data.get(
                        'conflict_object_index', None
                    ),
                    conflict_field=response_data.get('conflict_field', ''),
                    new_nested_object_data=new_object_data,
                    existing_nested_object_data=existing_object,
                )

                await message.answer(
                    detail_message,
                    reply_markup=nested_object_already_exist_inlin_kb,
                )

            case 'collection_already_exist':
                detail_message = response_data.get('detail')
                existing_object = response_data.get('existing_object')
                new_object_data = response_data.get('new_object')

                detail_message += (
                    f'\n\n<b>{new_object_data["title"]}</b>\n\n'
                    f'📖Коллекция из вашего списка коллекций:\n'
                    f'Коллекция: <b>{existing_object["title"]}</b>\n'
                    f'Описание: {existing_object["description"]}\n'
                )

                await state.update_data(
                    existing_nested_object_id=existing_object['id'],
                    conflict_nested_field='collections',
                    conflict_object_index=response_data.get(
                        'conflict_object_index', None
                    ),
                    conflict_field=response_data.get('conflict_field', ''),
                    new_nested_object_data=new_object_data,
                    existing_nested_object_data=existing_object,
                )

                await message.answer(
                    detail_message,
                    reply_markup=nested_object_already_exist_inlin_kb,
                )

            case _:
                detail_message = response_data.get('detail')
                await message.answer(detail_message)

    except KeyError as exception:
        logger.warning(f'KeyError was catched: {exception}')
        detail_message = response_data.get('detail')
        await message.answer(detail_message)


async def send_user_profile_answer(
    session: aiohttp.ClientSession,
    message: Message,
    state: FSMContext,
    response_data: dict,
    *args,
    **kwargs,
) -> None:
    """Sends user profile info."""
    username = response_data['username']
    first_name = response_data['first_name'] or '<i>Не заполнено</i>'
    words_count = response_data['words_count']
    profile_image_url = response_data['image']

    native_languages = (
        ', '.join(response_data['native_languages'])
        if response_data['native_languages']
        else '<i>Не заполнено</i>'
    )

    learning_languages_count = response_data['learning_languages_count']
    learning_languages = (
        '\n'.join(
            [
                '\t\t- '
                + language['language']['name_local']
                + ' ('
                + str(language['words_count'])
                + ')'
                for language in response_data['learning_languages']
            ]
        )
        if response_data['learning_languages']
        else '<i>Не заполнено</i>'
    )

    answer_text = '\n'.join(
        (
            f'<b>Профиль пользователя {username}</b>',
            '',
            f'<b>Имя:</b> {first_name}',
            f'<b>Родные языки:</b> {native_languages}',
            f'<b>Мощность словаря (общее кол-во слов):</b> {words_count}',
            '',
            f'<b>Количество изучаемых языков:</b> {learning_languages_count}',
            '<b>Изучаемые языки:</b>',
            f'{learning_languages}',
        )
    )

    if profile_image_url:
        # get image file from url
        headers = kwargs.get('headers', {})
        async with session.get(
            url=profile_image_url, headers=headers
        ) as image_response:
            profile_image = await image_response.content.read()
            profile_image_filename = profile_image_url.split('/')[-1]
        # send image file with text
        await message.answer_photo(
            photo=BufferedInputFile(
                file=profile_image, filename=profile_image_filename
            ),
            caption=answer_text,
            reply_markup=profile_kb,
        )
    # send only text
    else:
        await message.answer(
            answer_text,
            reply_markup=profile_kb,
        )


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

        answer_text = state_data.get(
            'vocabulary_answer_text',
            (
                f'Изучаемый язык: {language_name} ({language_name_local}) \n'
                f'Мощность словаря: {results_count} 🔥 \n\n'
            ),
        )

        # saving words to state by pages
        vocabulary_paginated = await save_paginated_words_to_state(
            state, results, results_count, language_name=language_name
        )
        markup = await generate_vocabulary_markup(state, vocabulary_paginated)

        # get learning language cover image
        cover_id = state_data.get('learning_languages_info')[language_name]['cover_id']

        await message.bot.send_photo(
            message.chat.id,
            photo=cover_id,
            caption=answer_text,
            reply_markup=markup,
        )

    except KeyError:
        results_count = response_data['count']
        results = response_data['results']

        answer_text = state_data.get(
            'vocabulary_answer_text',
            f'Все языки \nМощность словаря: {results_count} 🔥 \n\n',
        )

        # saving words to state by pages
        language_name = state_data.get('language_choose')
        vocabulary_paginated = await save_paginated_words_to_state(
            state, results, results_count, language_name=language_name
        )
        markup = await generate_vocabulary_markup(state, vocabulary_paginated)

        await message.answer(answer_text, reply_markup=markup)


async def send_vocabulary_answer_from_state_data(
    message: Message, state: FSMContext
) -> None:
    """Sends user vocabulary data from state data."""
    state_data = await state.get_data()
    answer_text = state_data.get('vocabulary_answer_text')
    language_name = state_data.get('language_choose')
    try:
        vocabulary_paginated = state_data.get('vocabulary_paginated')[language_name]
        vocabulary_words_count = state_data.get('vocabulary_words_count')[language_name]
    except KeyError:
        vocabulary_paginated = state_data.get('vocabulary_paginated')
        vocabulary_words_count = state_data.get('vocabulary_words_count')

    pages_total_amount = math.ceil(vocabulary_words_count / VOCABULARY_WORDS_PER_PAGE)
    await state.update_data(pages_total_amount=pages_total_amount)

    markup = await generate_vocabulary_markup(state, vocabulary_paginated)

    # if markup is None:  # make request to next page_num_global, save results to state, call generate_vocabulary_markup again (fix needed)

    if language_name:
        cover_id = state_data.get('learning_languages_info')[language_name]['cover_id']
        await message.bot.send_photo(
            message.chat.id,
            photo=cover_id,
            caption=answer_text,
            reply_markup=markup,
        )
    else:
        await message.answer(answer_text, reply_markup=markup)


async def send_collections_answer_from_state_data(
    message: Message, state: FSMContext, *args, **kwargs
) -> None:
    """Sends user collections data from state data."""
    state_data = await state.get_data()
    answer_text = state_data.get('collections_answer_text')
    collections_paginated = state_data.get('collections_paginated')
    collections_count = state_data.get('collections_count')

    pages_total_amount = math.ceil(collections_count / COLLECTIONS_PER_PAGE)
    await state.update_data(pages_total_amount=pages_total_amount)

    markup = await generate_collections_markup(state, collections_paginated, **kwargs)

    # if markup is None:  # make request to next page_num_global, save results to state, call generate_vocabulary_markup again

    await message.answer(answer_text, reply_markup=markup)


async def send_collections_answer(
    message: Message, state: FSMContext, response_data: dict, *args, **kwargs
) -> None:
    """Sends user collections data from API response data."""
    results_count = response_data['count']
    results = response_data['results']

    # set pages_total_amount value
    pages_total_amount = math.ceil(results_count / COLLECTIONS_PER_PAGE)
    await state.update_data(
        pages_total_amount=pages_total_amount, page_num=1, page_num_global=1
    )

    collections_paginated = await save_paginated_collections_to_state(
        state, results, results_count
    )
    markup = await generate_collections_markup(state, collections_paginated, **kwargs)

    state_data = await state.get_data()
    answer_text = state_data.get('collections_answer_text')

    await message.answer(
        answer_text,
        reply_markup=markup,
    )


async def send_word_profile_answer(
    message: Message,
    state: FSMContext,
    state_data: dict,
    response_data: dict,
    session: aiohttp.ClientSession,
    headers: dict,
) -> None:
    """Sends word profile from API response data."""
    # generate answer text
    answer_text = generate_word_profile_answer_text(state_data, response_data)

    # generate markup
    markup = await generate_word_profile_markup(response_data)

    try:
        images_data = state_data.get('images_ids')
        images_data = images_data if images_data else {}
        word_slug = state_data.get('word_slug')
        image_id = images_data[word_slug]

        await message.bot.send_photo(
            message.chat.id,
            photo=image_id,
            caption=answer_text,
            reply_markup=markup,
        )

    except KeyError:
        try:
            last_image_url = response_data['images'][-1]
            # get image file from url
            async with session.get(
                url=last_image_url, headers=headers
            ) as image_response:
                image = await image_response.content.read()
                image_filename = last_image_url.split('/')[-1]

            # send image file with text
            msg = await message.answer_photo(
                photo=BufferedInputFile(file=image, filename=image_filename),
                caption=answer_text,
                reply_markup=markup,
            )

            images_data = state_data.get('images_ids')
            images_data = images_data if images_data else {}
            word_slug = state_data.get('word_slug')
            images_data[word_slug] = msg.photo[-1].file_id
            await state.update_data(images_ids=images_data)

        except IndexError:
            # send only text
            await message.answer(answer_text, reply_markup=markup)


async def send_collection_profile_answer(
    message: Message,
    state: FSMContext,
    response_data: dict,
) -> None:
    """Sends collection profile from API response data."""
    # generate answer text
    words_languages = ', '.join(
        [
            f'{language_info["language__name"]} ({language_info["words_count"]})'
            for language_info in response_data['words_languages']
        ]
    )
    description = (
        response_data['description']
        if response_data['description']
        else '<i>Не указано</i>'
    )

    try:
        words_results = response_data['words']['results']
        words_count = response_data['words']['count']
    except TypeError:
        words_results = response_data['words']
        words_count = response_data['words_count']

    answer_text = (
        f'<b>{response_data["title"]}</b> \n\n'
        f'Описание: {description} \n'
        f'Языки: {words_languages} \n\n'
        f'Слова: {words_count}'
    )

    favorite = response_data['favorite']
    control_buttons = [
        InlineKeyboardButton(
            text='Добавить в избранное', callback_data='collection_favorite__post'
        )
    ]
    if favorite:
        answer_text += '\n\n⭐️ <i>Коллекция в избранном</i> \n'
        control_buttons = [
            InlineKeyboardButton(
                text='Удалить из избранного',
                callback_data='collection_favorite__delete',
            )
        ]

    # paginate collection words
    words = [
        {'text': word_info['text'], 'slug': word_info['slug']}
        for word_info in words_results
    ]
    words_paginated = paginate_values_list(words, VOCABULARY_WORDS_PER_PAGE)
    await state.update_data(
        pages_total_amount=len(words_paginated),
        page_num=1,
        page_num_global=1,
        vocabulary_paginated=words_paginated,
        vocabulary_words_list=words,
        vocabulary_words_count=len(words),
        vocabulary_answer_text=answer_text,
    )

    # generate markup
    markup = await generate_vocabulary_markup(
        state, words_paginated, control_buttons=control_buttons
    )

    await message.answer(answer_text, reply_markup=markup)
