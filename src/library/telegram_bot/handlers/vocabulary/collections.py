"""Collections CRUD handlres."""

import os
import logging
from http import HTTPStatus

import aiohttp
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from dotenv import load_dotenv

from keyboards.core import (
    cancel_inline_kb,
    return_button,
    cancel_button,
)
from keyboards.vocabulary import collections_kb, collection_profile_kb
from keyboards.generators import generate_learning_languages_markup
from states.vocabulary import Collections, CollectionUpdate, CollectionCreate

from ..urls import COLLECTIONS_URL
from ..utils import (
    send_error_message,
    send_unauthorized_response,
    send_collections_answer,
    save_learning_languages_to_state,
    api_request_logging,
    get_authentication_headers,
    send_collections_answer_from_state_data,
    send_collection_profile_answer,
    send_validation_errors,
    send_conflicts_errors,
    filter_by_date,
)
from .constants import (
    collections_ordering_filtering_pretty,
    ordering_type_pretty,
    MULTIPLE_WORDS_CREATE_AMOUNT_LIMIT,
)


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

router = Router()


# --- Collections list ---


@router.message(F.text == 'Коллекции')
async def collections_list(message: Message | CallbackQuery, state: FSMContext) -> None:
    """Sends user collections list from API response data or state data."""
    await state.update_data(pagination_handler=collections_list)
    await state.set_state(Collections.list_retrieve)

    if isinstance(message, CallbackQuery):
        message = message.message
    else:
        await message.answer(
            'Открываю коллекции...',
            reply_markup=collections_kb,
        )

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    collections_send_request = state_data.get('collections_send_request')

    if collections_send_request is False:
        await send_collections_answer_from_state_data(message, state)
        return None

    url = COLLECTIONS_URL
    await state.update_data(url=url)

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()
                    results_count = response_data['count']

                    if results_count == 0:
                        answer_text = (
                            f'📚 Коллекции: {results_count} \n\n'
                            f'Выберите пункт меню "Создать коллекцию" или '
                            f'добавляйте слова в коллекции при их создании, чтобы организовать свой словарь.'
                        )
                    else:
                        answer_text = f'📚 Коллекции: {results_count} \n\n'

                    await state.update_data(
                        collections_answer_text=answer_text,
                        collections_send_request=False,
                    )
                    await send_collections_answer(message, state, response_data)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Избранное', Collections.list_retrieve)
async def collections_favorites(message: Message, state: FSMContext) -> None:
    """Sends user favorite collections list from API response data."""
    await state.update_data(
        previous_state_handler=collections_list,
        pagination_handler=collections_favorites,
    )
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    url = COLLECTIONS_URL + 'favorites/'

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()
                    results_count = response_data['count']

                    await state.update_data(
                        collections_answer_text=f'⭐️Избранные коллекции: {results_count}',
                        collections_send_request=True,
                    )

                    await state.set_state(Collections.list_retrieve)
                    await send_collections_answer(message, state, response_data)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Поиск', Collections.list_retrieve)
async def collections_search(message: Message, state: FSMContext) -> None:
    """Sets state that awaits search value from user."""
    await state.set_state(Collections.search)
    await state.update_data(previous_state_handler=collections_list)

    await message.answer(
        'Введите поисковой запрос. Например: some collection name.',
        reply_markup=cancel_inline_kb,
    )


@router.message(Collections.search)
async def collections_search_proceed(message: Message, state: FSMContext) -> None:
    """Accepts search value, makes request with passed search value, sends collections answer."""
    if isinstance(message, CallbackQuery):
        await send_collections_answer_from_state_data(
            message.message, state, return_button=return_button
        )
        return None

    search_value = message.text
    await state.update_data(
        search=search_value,
        pagination_handler=collections_search_proceed,
    )

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
                    results_count = response_data['count']

                    await state.update_data(
                        collections_answer_text=f'Поиск: {search_value} 🔍 \nНайдено коллекций: {results_count}'
                    )

                    await send_collections_answer(
                        message, state, response_data, return_button=return_button
                    )
                    await state.set_state(Collections.list_retrieve)
                    await state.update_data(collections_send_request=True)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Сортировка', Collections.list_retrieve)
async def collections_ordering(message: Message, state: FSMContext) -> None:
    """Sends ordering field options."""
    await state.update_data(previous_state_handler=collections_list)
    await state.set_state(Collections.ordering)

    await message.answer(
        'Выберите сортировку из предложенных ниже:',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='По дате создания',
                        callback_data='collections_order_by__created',
                    ),
                    InlineKeyboardButton(
                        text='По количеству слов',
                        callback_data='collections_order_by__words_count',
                    ),
                ],
                [return_button],
            ],
        ),
    )


@router.callback_query(F.data.startswith('collections_order_by'))
async def collections_ordering_field_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Updates state with chosen ordering field, sends ordering type options."""
    order_field = callback_query.data.split('__')[-1]
    order_field_pretty = collections_ordering_filtering_pretty.get(order_field)
    await callback_query.answer(f'Выбрана сортировка: {order_field_pretty}')

    await callback_query.message.answer(
        'Выберите сортировку из предложенных ниже:',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='По убыванию',
                        callback_data=f'collections_order_type__{order_field}__descending',
                    ),
                    InlineKeyboardButton(
                        text='По возрастанию',
                        callback_data=f'collections_order_type__{order_field}__ascending',
                    ),
                ],
                [return_button],
            ],
        ),
    )


@router.callback_query(F.data.startswith('collections_order_type'))
async def collections_ordering_callback_proceed(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Accepts ordering type, makes request with chosen ordering, sends collections answer."""
    state_type = await state.get_state()
    if state_type == Collections.list_retrieve:
        await send_collections_answer_from_state_data(
            callback_query.message, state, return_button=return_button
        )
        return None

    order_type = callback_query.data.split('__')[-1]
    order_field = callback_query.data.split('__')[-2]

    order_field_pretty = collections_ordering_filtering_pretty.get(order_field)
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
                    answer_text = state_data.get('collections_answer_text')
                    answer_text += f'Коллекции сортированы {order_field_pretty.lower()} ({order_type_pretty.lower()})'

                    await state.update_data(
                        collections_answer_text=answer_text,
                        pagination_handler=collections_ordering_callback_proceed,
                    )

                    await send_collections_answer(
                        callback_query.message,
                        state,
                        response_data,
                        return_button=return_button,
                    )
                    await state.set_state(Collections.list_retrieve)
                    await state.update_data(collections_send_request=True)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(callback_query.message, state)

                case _:
                    await send_error_message(callback_query.message, state, response)


@router.message(F.text == 'Фильтры', Collections.list_retrieve)
async def collections_filtering(message: Message, state: FSMContext) -> None:
    """Sends filtering field options."""
    await state.update_data(previous_state_handler=collections_list)
    await state.set_state(Collections.filtering)

    await message.answer(
        'Выберите фильтр из предложенных ниже:',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='По дате создания',
                        callback_data='collections_filter_by__created',
                    ),
                    InlineKeyboardButton(
                        text='По языкам',
                        callback_data='collections_filter_by__language',
                    ),
                ],
                [return_button],
            ],
        ),
    )


@router.callback_query(F.data.startswith('collections_filter_by'))
async def collections_filtering_field_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Accepts chosen filter field, update state that awaits filter value or sends chosen filter options."""
    filter_field = callback_query.data.split('__')[-1]
    filter_field_pretty = collections_ordering_filtering_pretty.get(
        filter_field, filter_field
    )
    await callback_query.answer(f'Выбран фильтр: {filter_field_pretty}')
    await state.update_data(filter_field=filter_field)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)
    filtering = state_data.get('filtering') or {}

    message = callback_query.message

    match filter_field:
        case 'language':
            filtering[filter_field] = ''
            await state.update_data(filtering=filtering)

            # get available languages from API
            async with aiohttp.ClientSession() as session:
                await save_learning_languages_to_state(message, state, session, headers)

            markup = await generate_learning_languages_markup(
                state, callback_data='collections_language_filter'
            )

            await state.set_state(Collections.language_filter_value)

            await callback_query.message.answer(
                'Введите языки через запятую или выберите из предложенных ниже:',
                reply_markup=markup,
            )

        case 'created':
            filtering[filter_field] = ''
            await state.update_data(filtering=filtering)

            await message.answer(
                (
                    'Введите дату в формате YYYY-MM-DD (Пример: 2024-10-20). \n\n'
                    'Для фильтрации только по году или месяцу создания '
                    'введите только год или месяц (номер) соответственно. \n\n'
                    'Укажите через пробел перед датой знак &gt; или &lt; '
                    'для фильтра по значениям больше или меньше переданного соответственно.'
                ),
                reply_markup=cancel_inline_kb,
            )

            await state.set_state(Collections.date_filter_value)

        case _:
            raise AssertionError('no filter match')


@router.message(Collections.filtering)
async def collections_filtering_proceed(
    message: Message | CallbackQuery, state: FSMContext, *args, **kwargs
) -> None:
    """Accepts filter value, makes request with passed filter field, value, send collections answer."""
    if isinstance(message, CallbackQuery):
        await send_collections_answer_from_state_data(
            message.message, state, return_button=return_button
        )
        return None

    filter_value = kwargs.get('filter_value')
    filter_value = message.text if filter_value is None else filter_value

    state_data = await state.get_data()
    filter_field = state_data.get('filter_field')
    filter_field_pretty = collections_ordering_filtering_pretty.get(filter_field)
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
                    results_count = response_data['count']

                    filter_value = kwargs.get('filter_value_pretty') or filter_value
                    await state.update_data(
                        collections_answer_text=(
                            f'Фильтр: {filter_field_pretty} 👀 \n'
                            f'Значение: {filter_value} \n'
                            f'Найдено коллекций: {results_count}'
                        ),
                        pagination_handler=collections_filtering_proceed,
                    )

                    await send_collections_answer(
                        message, state, response_data, return_button=return_button
                    )
                    await state.set_state(Collections.list_retrieve)
                    await state.update_data(collections_send_request=True)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.callback_query(F.data.startswith('collections_language_filter'))
@router.message(Collections.language_filter_value)
async def collections_language_filter_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Calls filtering proceed with chosen language filter option."""
    state_data = await state.get_data()
    learning_languages_info = state_data.get('learning_languages_info')

    if isinstance(callback_query, CallbackQuery):
        language_name = callback_query.data.split('__')[-1]
        language_code = learning_languages_info[language_name]['isocode']
        await callback_query.answer(f'Выбран язык: {language_name}')
        message = callback_query.message
        filter_value = language_code

    else:
        message = callback_query
        passed_languages = message.text

        split_symbols = [',', ' ', ', ']
        languages = None
        for symb in split_symbols:
            match passed_languages.find(symb):
                case -1:
                    continue
                case _:
                    languages = passed_languages.split(symb)

        # convert to expected type if no split symbols were found
        if languages is None:
            languages = [passed_languages]

        # get languages isocodes
        languages_isocodes = []
        for language in languages:
            try:
                languages_isocodes.append(
                    learning_languages_info[language.capitalize()]['isocode']
                )
            except KeyError:
                await message.answer(
                    f'Язык {language} не найден среди ваших изучаемых языков. \nПроверьте правильность написания и повторите попытку.',
                    reply_markup=cancel_inline_kb,
                )
                return None

        filter_value = ','.join(languages_isocodes)

    await collections_filtering_proceed(message, state, filter_value=filter_value)


@router.message(Collections.date_filter_value)
async def collections_date_filter_proceed(
    message: Message, state: FSMContext, *args, **kwargs
) -> None:
    """Accepts date filter value, calls collections filtering proceed."""
    await filter_by_date(message, state, filter_handler=collections_filtering_proceed)


# --- Collection profile ---


@router.callback_query(F.data.startswith('collection_profile'))
async def collection_profile_callback(
    callback_query: CallbackQuery | Message, state: FSMContext, *args, **kwargs
) -> None:
    """Sets retrieve collection profile state, makes API request to get collection info, sends collection profile info."""
    await state.update_data(previous_state_handler=collections_list)

    await state.set_state(Collections.retrieve)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    if isinstance(callback_query, CallbackQuery):
        message: Message = callback_query.message

        collections_list_info: list = state_data.get('collections_list')
        collection_index = int(callback_query.data.split('__')[-1])
        collection_info = collections_list_info[collection_index]
        collection_title = collection_info['title']
        collection_slug = collection_info['slug']

        await callback_query.answer(f'Выбрана коллекция: {collection_title}')
        await state.update_data(collection_slug=collection_slug)
        await state.update_data(collection_title=collection_title)

    else:
        message: Message = callback_query
        collection_slug = state_data.get('collection_slug')
        collection_title = state_data.get('collection_title')

    await message.answer(
        f'Открываю коллекцию {collection_title}...',
        reply_markup=collection_profile_kb,
    )

    url = COLLECTIONS_URL + collection_slug + '/'
    await state.update_data(url=url)

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()
                    await state.update_data(response_data=response_data)
                    await send_collection_profile_answer(message, state, response_data)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Добавить слова', Collections.retrieve)
async def collection_add_words(message: Message, state: FSMContext) -> None:
    """Adding words to collection start, sets state that awaits words language."""
    await state.update_data(previous_state_handler=collection_profile_callback)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    # generate inline keyboard
    async with aiohttp.ClientSession() as session:
        await save_learning_languages_to_state(message, state, session, headers)

    markup = await generate_learning_languages_markup(
        state, callback_data='collection_add_words_language'
    )

    await state.set_state(Collections.new_words_language)
    await message.answer(
        'Введите язык новых слов или выберите изучаемый язык:',
        reply_markup=markup,
    )


@router.message(Collections.new_words_language)
@router.callback_query(F.data.startswith('collection_add_words_language'))
async def collection_add_words_language_proceed(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Updates state data with passed language name from message text, sets state that awaits words."""
    if isinstance(callback_query, CallbackQuery):
        language_name = callback_query.data.split('__')[-1]
        await callback_query.answer(language_name)
        message = callback_query.message
    else:
        message = callback_query
        language_name = message.text.capitalize()

    await state.update_data(language=language_name)
    await state.set_state(Collections.new_words)

    await message.answer(
        (
            f'<b>Язык:</b> {language_name}\n\n'
            f'Введите слова или фразы, разделяя их знаком ;'
        ),
        reply_markup=cancel_inline_kb,
    )


@router.message(Collections.new_words)
async def collection_add_words_proceed(message: Message, state: FSMContext):
    """Accepts words list, makes API request, sends updated collection profile."""
    await state.update_data(previous_state_handler=collection_profile_callback)
    await message.answer('Сохранение...')

    state_data = await state.get_data()
    language_name = state_data.get('language')

    # handle passed words
    new_words_value = message.text
    split_symbols = [';', '; ']

    new_words = None
    for symb in split_symbols:
        match new_words_value.find(symb):
            case -1:
                continue
            case _:
                new_words = new_words_value.split(symb)

    # convert to expected type if no split symbols were found
    if not new_words:
        new_words = [new_words_value]

    # check words amount limit
    if len(new_words) > MULTIPLE_WORDS_CREATE_AMOUNT_LIMIT:
        await message.answer(
            f'Вы превысили количество новых слов за раз: {MULTIPLE_WORDS_CREATE_AMOUNT_LIMIT} \nПожалуйста, уменьшите количество слов и повторите попытку.',
            reply_markup=cancel_inline_kb,
        )
        return None

    # sending request to API
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)
    url = state_data.get('url') + 'add-words/'
    request_data = [{'language': language_name, 'text': word} for word in new_words]

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='post', data=request_data)
        async with session.post(
            url=url, headers=headers, json=request_data
        ) as response:
            match response.status:
                case HTTPStatus.CREATED:
                    await message.answer(f'Добавлено слов: {len(request_data)}')
                    response_data: dict = await response.json()
                    await state.update_data(
                        response_data=response_data, vocabulary_send_request=True
                    )
                    await send_collection_profile_answer(message, state, response_data)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Редактировать', Collections.retrieve)
async def collection_update(message: Message, state: FSMContext) -> None:
    """Sets update collection state, sends update options to choose."""
    await state.update_data(previous_state_handler=collection_profile_callback)

    await message.answer(
        'Выберите данные для редактирования:',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Название', callback_data='collection_update_title'
                    ),
                    InlineKeyboardButton(
                        text='Описание', callback_data='collection_update_description'
                    ),
                ],
                [cancel_button],
            ]
        ),
    )


@router.callback_query(F.data.startswith('collection_update_title'))
async def collection_update_title_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Sets state that awaits collection title."""
    await callback_query.answer('Редактировать: Название')

    await state.set_state(CollectionUpdate.title)

    await callback_query.message.answer(
        'Введите новое название коллекции.',
        reply_markup=cancel_inline_kb,
    )


@router.callback_query(F.data.startswith('collection_update_description'))
async def collection_update_description_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Sets state that awaits collection description."""
    await callback_query.answer('Редактировать: Описание')

    await state.set_state(CollectionUpdate.description)

    await callback_query.message.answer(
        'Введите новое описание коллекции.',
        reply_markup=cancel_inline_kb,
    )


@router.message(CollectionUpdate.title)
@router.message(CollectionUpdate.description)
async def collection_update_proceed(
    message: Message | CallbackQuery, state: FSMContext
):
    """Makes API request to update with collection with passed data, send updated collection profile."""
    new_value = message.text
    state_type = await state.get_state()

    match state_type:
        case CollectionUpdate.title:
            await state.update_data(title=new_value)
            request_data = {'title': new_value}
        case CollectionUpdate.description:
            await state.update_data(description=new_value)
            request_data = {'description': new_value}

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)
    url = state_data.get('url')

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='patch', data=request_data)
        async with session.patch(
            url=url, json=request_data, headers=headers
        ) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()
                    collection_title = response_data.get('title')
                    collection_slug = response_data.get('slug')

                    await state.set_state(Collections.retrieve)
                    await state.update_data(
                        previous_state_handler=collections_list,
                        collection_title=collection_title,
                        collection_slug=collection_slug,
                        collections_send_request=True,
                        url=COLLECTIONS_URL + collection_slug + '/',
                    )

                    await message.answer(
                        f'Открываю коллекцию {collection_title}...',
                        reply_markup=collection_profile_kb,
                    )

                    await send_collection_profile_answer(message, state, response_data)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case HTTPStatus.BAD_REQUEST:
                    await send_validation_errors(message, state, response)

                case HTTPStatus.CONFLICT:
                    await send_conflicts_errors(message, state, response)

                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Удалить', Collections.retrieve)
async def collection_delete(message: Message, state: FSMContext) -> None:
    """Sends confirmation message."""
    await state.update_data(previous_state_handler=collection_profile_callback)

    state_data = await state.get_data()
    collection_title = state_data.get('collection_title')

    await message.answer(
        f'Вы уверены, что хотите удалить коллекцию {collection_title}?',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Удалить', callback_data='collection_delete'
                    ),
                ],
                [
                    cancel_button,
                ],
            ]
        ),
    )


@router.callback_query(F.data.startswith('collection_delete'))
async def collection_delete_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Makes API request to delete collection."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)
    url = state_data.get('url')

    await callback_query.answer('Удаление')

    async with aiohttp.ClientSession() as session:
        message = callback_query.message
        api_request_logging(url, headers=headers, method='delete')
        async with session.delete(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK | HTTPStatus.NO_CONTENT:
                    await message.answer('Коллекция удалена.')
                    await state.update_data(collections_send_request=True)
                    await collections_list(message, state)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.callback_query(F.data.startswith('collection_favorite'))
async def collection_favorite_callback(
    callback_query: CallbackQuery | Message, state: FSMContext, *args, **kwargs
) -> None:
    """Makes API request to add or remove collection from favorites."""
    message: Message = callback_query.message
    method = callback_query.data.split('__')[-1]

    match method:
        case 'post':
            await callback_query.answer('Добавление в избранное')
            await message.answer('Добавление в избранное...')
        case 'delete':
            await callback_query.answer('Удаление из избранного')
            await message.answer('Удаление из избранного...')

    state_data = await state.get_data()
    collection_slug = state_data.get('collection_slug')
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    url = COLLECTIONS_URL + collection_slug + '/' + 'favorite/'

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method=method)
        async with session.__getattribute__(method)(
            url=url, headers=headers
        ) as response:
            match response.status:
                case HTTPStatus.OK | HTTPStatus.CREATED:
                    response_data: dict = await response.json()
                    response_data['words'] = {}
                    response_data['words']['results'] = state_data.get(
                        'vocabulary_words_list'
                    )
                    response_data['words']['count'] = state_data.get(
                        'vocabulary_words_count'
                    )
                    await send_collection_profile_answer(message, state, response_data)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(callback_query.message, state)

                case _:
                    await send_error_message(callback_query.message, state, response)


# --- Collection create ---


@router.message(F.text == 'Создать коллекцию')
async def collection_create(message: Message, state: FSMContext) -> None:
    """Collection create start, sets state that awaits new collection title."""
    await state.update_data(previous_state_handler=collections_list)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    async with aiohttp.ClientSession() as session:
        await save_learning_languages_to_state(message, state, session, headers)

    await state.set_state(CollectionCreate.title)

    await message.answer(
        'Введите название коллекции.',
        reply_markup=cancel_inline_kb,
    )


@router.message(CollectionCreate.title)
async def collection_create_title_proceed(message: Message, state: FSMContext) -> None:
    """Updates state data with passed title, sets state that awaits collection description."""
    await state.update_data(title=message.text)
    await state.set_state(CollectionCreate.description)

    await message.answer(
        'Введите описание коллекции.',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Пропустить', callback_data='skip_description'
                    )
                ],
                [cancel_button],
            ]
        ),
    )


@router.message(CollectionCreate.description)
@router.callback_query(F.data == 'skip_description')
async def collection_create_description_proceed(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Update state data with passed description, sets state that awaits collection words language."""
    if isinstance(callback_query, CallbackQuery):
        await callback_query.answer('Пропустить')
        message = callback_query.message
    else:
        message = callback_query
        await state.update_data(
            description=message.text,
        )

    # generate inline keyboard
    markup = await generate_learning_languages_markup(
        state,
        callback_data='collection_create_words_language',
        control_buttons=[
            InlineKeyboardButton(text='Пропустить', callback_data='skip_words')
        ],
    )

    await state.set_state(CollectionCreate.words_language)
    await message.answer(
        'Введите язык новых слов или выберите изучаемый язык:',
        reply_markup=markup,
    )


@router.message(CollectionCreate.words_language)
@router.callback_query(F.data.startswith('collection_create_words_language'))
async def collection_create_words_language_proceed(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Updates state data with passed language name from message text, sets state that awaits words."""
    if isinstance(callback_query, CallbackQuery):
        if callback_query.data == 'skip_words':
            await callback_query.answer('Пропустить')
            message = callback_query.message
        else:
            language_name = callback_query.data.split('__')[-1]
            await callback_query.answer(language_name)
            message = callback_query.message
    else:
        message = callback_query
        language_name = message.text.capitalize()

    await state.update_data(words_language=language_name)
    await state.set_state(CollectionCreate.words)

    await message.answer(
        'Введите слова, которые хотите добавить в эту коллекцию, разделяя их знаком ;',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Пропустить', callback_data='skip_words')],
                [cancel_button],
            ]
        ),
    )


@router.message(CollectionCreate.words)
@router.callback_query(F.data == 'skip_words')
async def collection_create_proceed(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Accepts words list, make API request to create collection with passed data, sends new collection profile."""
    if isinstance(callback_query, CallbackQuery):
        await callback_query.answer('Пропустить')
        message = callback_query.message
        words = None
    else:
        # handle passed words
        message = callback_query
        words_value = message.text
        split_symbols = [';', '; ']

        words = None
        for symb in split_symbols:
            match words_value.find(symb):
                case -1:
                    continue
                case _:
                    words = words_value.split(symb)

        # convert to expected type if no split symbols were found
        if not words:
            words = [words_value]

    await message.answer('Сохранение...')

    # sending request to API
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)
    url = COLLECTIONS_URL
    request_data = {
        'title': state_data.get('title'),
        'description': state_data.get('description', ''),
    }
    if words:
        language_name = state_data.get('words_language')
        request_data['words'] = [
            {'language': language_name, 'text': word} for word in words
        ]

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='post', data=request_data)
        async with session.post(
            url=url, headers=headers, json=request_data
        ) as response:
            match response.status:
                case HTTPStatus.CREATED:
                    response_data: dict = await response.json()

                    collection_title = response_data.get('title')
                    collection_slug = response_data.get('slug')

                    await state.set_state(Collections.retrieve)
                    await state.update_data(
                        previous_state_handler=collections_list,
                        collection_title=collection_title,
                        collection_slug=collection_slug,
                        collections_send_request=True,
                        url=COLLECTIONS_URL + collection_slug + '/',
                    )

                    await message.answer(
                        f'Открываю коллекцию {collection_title}...',
                        reply_markup=collection_profile_kb,
                    )

                    await send_collection_profile_answer(message, state, response_data)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case HTTPStatus.BAD_REQUEST:
                    await send_validation_errors(message, state, response)

                case HTTPStatus.CONFLICT:
                    await send_conflicts_errors(message, state, response)

                case _:
                    await send_error_message(message, state, response)
