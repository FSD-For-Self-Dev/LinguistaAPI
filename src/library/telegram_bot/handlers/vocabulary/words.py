"""Words CRUD handlres."""

import os
import logging
from http import HTTPStatus
import io
import base64
import math

import aiohttp
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile,
    InputMediaPhoto,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from keyboards.core import (
    cancel_button,
    cancel_inline_kb,
    return_button,
    return_inline_kb,
)
from keyboards.vocabulary import word_profile_kb, vocabulary_kb
from keyboards.generators import (
    generate_word_customization_markup,
    generate_learning_languages_markup,
    generate_collections_markup,
    generate_words_multiple_create_markup,
    generate_additions_list_markup,
    generate_vocabulary_markup,
)
from states.vocabulary import WordProfile, WordCreate, Vocabulary

from ..urls import VOCABULARY_URL, COLLECTIONS_URL, API_URL
from ..utils import (
    send_error_message,
    send_unauthorized_response,
    send_vocabulary_answer,
    send_validation_errors,
    send_conflicts_errors,
    save_types_info_to_state,
    save_native_languages_to_state,
    save_paginated_collections_to_state,
    send_word_profile_answer,
    api_request_logging,
    get_authentication_headers,
    paginate_values_list,
    generate_validation_errors_answer_text,
    generate_word_create_request_data,
    save_learning_languages_to_state,
)
from .vocabulary import vocabulary_choose_language_callback
from .constants import (
    LEARNING_LANGUAGES_MARKUP_SIZE,
    MULTIPLE_WORDS_CREATE_AMOUNT_LIMIT,
    VOCABULARY_WORDS_PER_PAGE,
    COLLECTIONS_PER_PAGE,
    additions_pretty,
    fields_pretty,
)


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

router = Router()


# --- Word profile ---


@router.callback_query(F.data.startswith('word_profile'))
@router.callback_query(F.data.startswith('wp_word_profile'))
async def word_profile_callback(
    callback_query: CallbackQuery | Message, state: FSMContext, *args, **kwargs
) -> None:
    """Sets retrieve word profile state, makes API request to get word info, sends word profile info."""
    await state.update_data(previous_state_handler=vocabulary_choose_language_callback)
    await state.set_state(WordProfile.retrieve)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)

    if isinstance(callback_query, CallbackQuery):
        message: Message = callback_query.message
        language_name = state_data.get('language_choose')

        try:
            vocabulary_words_list: list = state_data.get('vocabulary_words_list')[
                language_name
            ]
        except TypeError:
            vocabulary_words_list: list = state_data.get('vocabulary_words_list')

        word_index = int(callback_query.data.split('__')[-1])
        if callback_query.data.startswith('wp_word_profile'):
            # retrieve word from synonyms, antonyms, forms, similars list
            await state.update_data(previous_state_handler=additions_list_callback)
            additions_field = state_data.get('additions_field')
            word_info = state_data.get(f'{additions_field}_list')[word_index]
        else:
            word_info = vocabulary_words_list[word_index]
        word_text = word_info['text']
        word_slug = word_info['slug']

        await callback_query.answer(f'Выбрано слово: {word_text}')
        await state.update_data(
            word_slug=word_slug,
            word_text=word_text,
        )

    else:
        message: Message = callback_query
        word_slug = state_data.get('word_slug')
        word_text = state_data.get('word_text')

    await message.answer(
        f'Открываю профиль слова {word_text}...',
        reply_markup=word_profile_kb,
    )

    url = VOCABULARY_URL + word_slug
    await state.update_data(url=url)

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()
                    await state.update_data(response_data=response_data)
                    await send_word_profile_answer(
                        message, state, state_data, response_data, session, headers
                    )

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(callback_query.message, state)

                case _:
                    await send_error_message(callback_query.message, state, response)


@router.callback_query(F.data.startswith('word_favorite'))
async def word_favorite_callback(
    callback_query: CallbackQuery | Message, state: FSMContext, *args, **kwargs
) -> None:
    """Makes API request to add or remove word from favorites."""
    await state.update_data(previous_state_handler=vocabulary_choose_language_callback)

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
    word_slug = state_data.get('word_slug')
    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)

    url = VOCABULARY_URL + word_slug + '/' + 'favorite/'
    await state.update_data(url=url)

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method=method)
        async with session.__getattribute__(method)(
            url=url, headers=headers
        ) as response:
            match response.status:
                case HTTPStatus.OK | HTTPStatus.CREATED:
                    response_data: dict = await response.json()
                    await send_word_profile_answer(
                        message, state, state_data, response_data, session, headers
                    )

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(callback_query.message, state)

                case _:
                    await send_error_message(callback_query.message, state, response)


@router.callback_query(F.data.startswith('problematic_toggle'))
async def problematic_toggle_callback(
    callback_query: CallbackQuery | Message, state: FSMContext, *args, **kwargs
) -> None:
    """Makes API request to add or remove problematic word status."""
    await state.update_data(previous_state_handler=word_profile_callback)

    message: Message = callback_query.message
    method = callback_query.data.split('__')[-1]

    match method:
        case 'post':
            await callback_query.answer('Добавление в проблемные')
            await message.answer('Добавление в проблемные...')
        case 'delete':
            await callback_query.answer('Удаление из проблемных')
            await message.answer('Удаление из проблемных...')

    state_data = await state.get_data()
    word_slug = state_data.get('word_slug')
    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)

    url = VOCABULARY_URL + word_slug + '/' + 'problematic-toggle/'
    await state.update_data(url=url)

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='post')
        async with session.post(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK | HTTPStatus.CREATED:
                    response_data: dict = await response.json()
                    await send_word_profile_answer(
                        message, state, state_data, response_data, session, headers
                    )

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


async def fill_word_state_data_with_response_data(
    state: FSMContext, word_profile_response_data: dict
) -> None:
    """Fills word state data in expected format with word profile response data."""
    fields_to_fill = (
        list(additions_pretty)
        + [f'{additions_field}_count' for additions_field in additions_pretty]
        + ['language', 'text']
    )

    for field in fields_to_fill:
        match field:
            case 'examples' | 'definitions':
                field_data = [
                    data['text'] for data in word_profile_response_data[field]
                ]

            case 'synonyms' | 'antonyms' | 'forms' | 'similars':
                field_data = [
                    data['from_word']['text']
                    for data in word_profile_response_data[field]
                ]
                await state.update_data(
                    {
                        f'{field}_list': [
                            {
                                'text': data['from_word']['text'],
                                'slug': data['from_word']['slug'],
                            }
                            for data in word_profile_response_data[field]
                        ]
                    }
                )

            case 'form_groups' | 'tags':
                field_data = [
                    data['name'] for data in word_profile_response_data[field]
                ]

            case 'collections':
                field_data = [
                    data['title'] for data in word_profile_response_data[field]
                ]
                await save_paginated_collections_to_state(
                    state,
                    collections=word_profile_response_data[field],
                    collections_count=word_profile_response_data[f'{field}_count'],
                    collections_send_request=True,
                )

            case 'translations':
                field_data = [
                    (data['language'], data['text'])
                    for data in word_profile_response_data[field]
                ]

            case 'image_associations':
                # get image file from url
                async with aiohttp.ClientSession() as session:
                    field_data = []

                    for image_url in word_profile_response_data['images']:
                        async with session.get(url=image_url) as image_response:
                            image = await image_response.content.read()
                            image_filename = image_url.split('/')[-1]

                        encoded_image = base64.b64encode(image).decode('utf-8')
                        field_data.append(
                            (
                                BufferedInputFile(file=image, filename=image_filename),
                                encoded_image,
                            )
                        )

            case 'image_associations_count':
                field_data = word_profile_response_data['images_count']

            case 'types_count':
                field_data = len(word_profile_response_data['types'])

            case 'form_groups_count':
                field_data = len(word_profile_response_data['form_groups'])

            case 'tags_count':
                field_data = len(word_profile_response_data['tags'])

            case 'note_count':
                pass

            case _:
                field_data = word_profile_response_data[field]

        await state.update_data({field: field_data})


@router.message(F.text == 'Редактировать', WordProfile.retrieve)
async def word_update(message: Message, state: FSMContext) -> None:
    """Sets update word state, calls word create handler with current word data."""
    await state.update_data(
        previous_state_handler=word_profile_callback,
        control_buttons=None,
    )

    state_data = await state.get_data()
    profile_response_data = state_data.get('response_data')
    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)

    async with aiohttp.ClientSession() as session:
        await save_native_languages_to_state(message, state, session, headers)
        await save_types_info_to_state(message, state, session, headers)

    await fill_word_state_data_with_response_data(state, profile_response_data)

    word_slug = state_data.get('word_slug')
    url = VOCABULARY_URL + f'{word_slug}/'
    method = 'patch'
    await state.update_data(url=url, method=method)

    # use create logic
    await word_create_text_proceed(message, state)


@router.message(F.text == 'Удалить', WordProfile.retrieve)
async def word_delete(message: Message, state: FSMContext) -> None:
    """Sends confirmation message."""
    await state.update_data(previous_state_handler=word_profile_callback)

    state_data = await state.get_data()
    word_text = state_data.get('word_text')

    await message.answer(
        f'Вы уверены, что хотите удалить слово {word_text}?',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Удалить', callback_data='word_delete'),
                ],
                [
                    cancel_button,
                ],
            ]
        ),
    )


@router.callback_query(F.data.startswith('word_delete'))
async def word_delete_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Makes API request to delete word from user vocabulary."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)
    url = state_data.get('url')

    await callback_query.answer('Удаление')

    async with aiohttp.ClientSession() as session:
        message = callback_query.message
        api_request_logging(url, headers=headers, method='delete')
        async with session.delete(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK | HTTPStatus.NO_CONTENT:
                    await message.answer('Слово удалено из вашего словаря.')
                    await state.update_data(vocabulary_send_request=True)
                    await vocabulary_choose_language_callback(message, state)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


@router.callback_query(F.data.startswith('additions_list'))
async def additions_list_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Sends current word additions list from state data."""
    await state.update_data(previous_state_handler=word_profile_callback)

    state_data = await state.get_data()

    if isinstance(callback_query, CallbackQuery):
        additions_field = callback_query.data.split('__')[-1]
        additions_field_pretty = additions_pretty.get(additions_field)[0]
        await callback_query.answer(additions_field_pretty)
        await fill_word_state_data_with_response_data(
            state, state_data.get('response_data')
        )
        await state.update_data(additions_field=additions_field)
        message: Message = callback_query.message
    else:
        additions_field = state_data.get('additions_field')
        additions_field_pretty = additions_pretty.get(additions_field)[0]
        message: Message = callback_query

    state_data = await state.get_data()
    additions_data = state_data.get(additions_field)
    additions_count = state_data.get(f'{additions_field}_count')

    if additions_field == 'image_associations':
        # send media group from buffered image files in state data
        images_group = []
        for image_info in additions_data:
            images_group.append(InputMediaPhoto(media=image_info[0]))
        await message.answer_media_group(images_group)

    answer_text = f'{additions_field_pretty}: {additions_count}'
    markup = await generate_additions_list_markup(additions_field, additions_data)

    await message.answer(
        answer_text,
        reply_markup=markup,
    )


@router.callback_query(F.data.startswith('additions_profile'))
async def additions_profile_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Sends addition profile with related words from API response data."""
    await state.update_data(previous_state_handler=additions_list_callback)

    state_data = await state.get_data()
    additions_field = state_data.get('additions_field')
    word_profile_response_data = state_data.get('response_data')
    addition_index = int(callback_query.data.split('__')[-1])
    addition_slug = word_profile_response_data[additions_field][addition_index]['slug']

    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)
    url = API_URL + additions_field + '/' + addition_slug + '/'
    await state.update_data(url=url)

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method='get')
        async with session.get(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()
                    words_count = response_data['words']['count']

                    match additions_field:
                        case 'translations':
                            translation = response_data['text']
                            await callback_query.answer(translation)
                            answer_text = (
                                f'Перевод: <b>{translation}</b>\n\n'
                                f'Слов с этим переводом: {words_count}'
                            )
                        case 'examples':
                            example = response_data['text']
                            await callback_query.answer(example)
                            answer_text = (
                                f'Пример: <b>{example}</b>\n'
                                f'Перевод: {response_data["translation"]}\n\n'
                                f'Слов с этим примером: {words_count}'
                            )
                        case 'definitions':
                            definition = response_data['text']
                            await callback_query.answer(definition)
                            answer_text = (
                                f'Определение: <b>{definition}</b>\n'
                                f'Перевод: {response_data["translation"]}\n\n'
                                f'Слов с этим определением: {words_count}'
                            )

                    # paginate words
                    words = [
                        {'text': word_info['text'], 'slug': word_info['slug']}
                        for word_info in response_data['words']['results']
                    ]
                    words_paginated = await paginate_values_list(
                        words, VOCABULARY_WORDS_PER_PAGE
                    )
                    await state.update_data(
                        pages_total_amount=len(words_paginated),
                        page_num=1,
                        vocabulary_paginated=words_paginated,
                        vocabulary_words_list=words,
                        vocabulary_words_count=len(words),
                        vocabulary_answer_text=answer_text,
                    )

                    # generate markup with words
                    markup = await generate_vocabulary_markup(state, words_paginated)

                    await callback_query.message.answer(
                        answer_text,
                        reply_markup=markup,
                    )

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(callback_query.message, state)

                case _:
                    await send_error_message(callback_query.message, state, response)


# --- Word create ---


@router.message(F.text == 'Добавить новое слово')
async def word_create(message: Message, state: FSMContext) -> None:
    """Sets state that awaits for language name or word text, if language name already defined."""
    await state.update_data(
        previous_state_handler=vocabulary_choose_language_callback,
        create_start=True,
        control_buttons=None,
    )

    url = VOCABULARY_URL
    method = 'post'
    await state.update_data(url=url, method=method)

    await state.set_state(WordCreate.language)

    state_data = await state.get_data()
    language_name = state_data.get('language_choose')

    if language_name:
        await state.update_data(language=language_name)
        await state.set_state(WordCreate.text)
        await message.answer(
            (f'<b>Язык:</b> {language_name}\n\n' f'Введите слово или фразу.'),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text='Сменить язык',
                            callback_data='word_create_change_language',
                        ),
                    ],
                    [
                        cancel_button,
                    ],
                ]
            ),
        )
    else:
        # generate inline keyboard
        markup = await generate_learning_languages_markup(state)
        await message.answer(
            'Введите язык нового слова или выберите изучаемый язык:',
            reply_markup=markup,
        )

    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)

    async with aiohttp.ClientSession() as session:
        await save_native_languages_to_state(message, state, session, headers)
        await save_types_info_to_state(message, state, session, headers)


@router.callback_query(F.data.startswith('word_create_change_language'))
async def word_create_change_language_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Sets state that awaits language name."""
    await callback_query.answer('Сменить язык')
    await state.set_state(WordCreate.language)
    markup = await generate_learning_languages_markup(state)
    await callback_query.message.answer(
        'Введите язык нового слова или выберите изучаемый язык:',
        reply_markup=markup,
    )


@router.message(WordCreate.language)
@router.callback_query(F.data.startswith('word_create_language'))
async def word_create_language_proceed(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Updates state data with passed language name from message text, sets state that awaits word text."""
    if isinstance(callback_query, CallbackQuery):
        language_name = callback_query.data.split('__')[-1]
        await callback_query.answer(language_name)
        message = callback_query.message
    else:
        message = callback_query
        language_name = message.text.capitalize()

    await state.update_data(language=language_name)
    await state.set_state(WordCreate.text)

    await message.answer(
        (f'<b>Язык:</b> {language_name}\n\n' f'Введите слово или фразу.'),
        reply_markup=cancel_inline_kb,
    )


@router.message(WordCreate.text)
async def word_create_text_proceed(message: Message | CallbackQuery, state: FSMContext):
    """Accepts word text, sets state that awaits new text, sends customization info, confirm button."""
    await state.update_data(previous_state_handler=vocabulary_choose_language_callback)

    state_data = await state.get_data()
    language_name = state_data.get('language')
    text = state_data.get('text')
    create_start = state_data.get('create_start')
    control_buttons = state_data.get('control_buttons')

    await state.set_state(WordCreate.text_edit)

    if create_start:
        text = message.text
        await state.update_data(text=text, create_start=False)

        for additions_field in additions_pretty:
            await state.update_data({additions_field: []})
            await state.update_data({f'{additions_field}_count': 0})
            state_data = await state.get_data()

    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.add(
        InlineKeyboardButton(
            text=f'Переводы {state_data.get("translations_count")}',
            callback_data='word_customizing__translations',
        ),
        InlineKeyboardButton(
            text=f'Примеры {state_data.get("examples_count")}',
            callback_data='word_customizing__examples',
        ),
        InlineKeyboardButton(
            text=f'Определения {state_data.get("definitions_count")}',
            callback_data='word_customizing__definitions',
        ),
        InlineKeyboardButton(
            text=f'Картинки-ассоциации {state_data.get("image_associations_count")}',
            callback_data='word_customizing__image_associations',
        ),
        InlineKeyboardButton(
            text=f'Синонимы {state_data.get("synonyms_count")}',
            callback_data='word_customizing__synonyms',
        ),
        InlineKeyboardButton(
            text=f'Антонимы {state_data.get("antonyms_count")}',
            callback_data='word_customizing__antonyms',
        ),
        InlineKeyboardButton(
            text=f'Формы {state_data.get("forms_count")}',
            callback_data='word_customizing__forms',
        ),
        InlineKeyboardButton(
            text=f'Похожие слова {state_data.get("similars_count")}',
            callback_data='word_customizing__similars',
        ),
        InlineKeyboardButton(
            text=f'Коллекции {state_data.get("collections_count")}',
            callback_data='word_customizing__collections',
        ),
        InlineKeyboardButton(
            text='Добавить заметку', callback_data='word_customizing__note'
        ),
    )
    keyboard_builder.adjust(2)
    keyboard_builder.row(
        InlineKeyboardButton(
            text=f'Типы (части речи) {state_data.get("types_count")}',
            callback_data='word_customizing__types',
        ),
        InlineKeyboardButton(
            text=f'Группы форм (форма) {state_data.get("form_groups_count")}',
            callback_data='word_customizing__form_groups',
        ),
        InlineKeyboardButton(
            text=f'Теги {state_data.get("tags_count")}',
            callback_data='word_customizing__tags',
        ),
    )
    if control_buttons is None:
        keyboard_builder.row(
            InlineKeyboardButton(text='Сохранить', callback_data='save_word')
        )
        keyboard_builder.row(cancel_button)
    else:
        for button in control_buttons:
            keyboard_builder.row(button)

    if isinstance(message, CallbackQuery):
        message: Message = message.message

    await message.answer(
        (
            f'<b>Язык:</b> {language_name}\n'
            f'<b>Слово:</b> {text}\n\n'
            f'Кастомизируйте слово или нажмите Сохранить для завершения создания. \n\n'
            f'Введите слово еще раз, чтобы редактировать его. '
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export()),
    )


@router.message(WordCreate.text_edit)
async def word_create_text_edit_proceed(
    message: Message | CallbackQuery, state: FSMContext
):
    """Updates state data with new text."""
    new_text = message.text
    await state.update_data(text=new_text)
    await word_create_text_proceed(message, state)


@router.callback_query(F.data.startswith('word_customizing'))
async def word_create_customization_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Returns word additions current data with update, delete options, sets state that awaits new values."""
    await state.update_data(previous_state_handler=word_create_text_proceed)

    await state.set_state(WordCreate.customizing_value)

    state_data = await state.get_data()
    language_name = state_data.get('language')
    word_text = state_data.get('text')

    if isinstance(callback_query, CallbackQuery):
        additions_field = callback_query.data.split('__')[-1]
        await state.update_data(current_customizing_field=additions_field)

        (
            additions_field_pretty_name,
            additions_field_description,
        ) = additions_pretty.get(additions_field)
        await callback_query.answer(additions_field_pretty_name)

        message: Message = callback_query.message

    else:
        additions_field = state_data.get('current_customizing_field')
        (
            additions_field_pretty_name,
            additions_field_description,
        ) = additions_pretty.get(additions_field)

        message: Message = callback_query

    additions_data = state_data.get(additions_field)

    match additions_field:
        case 'types':
            types_available = ', '.join(
                [type_info['name'] for type_info in state_data.get('types_available')]
            )
            answer_text = (
                f'<b>Язык:</b> {language_name}\n'
                f'<b>Слово:</b> {word_text}\n\n'
                f'<b>{additions_field_pretty_name}:</b> {len(additions_data)} \n\n'
                f'{additions_field_description} \n\n'
                f'<b>Доступные типы:</b> {types_available} \n\n'
                f'Нажмите Вернуться назад, чтобы вернуться к слову.'
            )
            markup = return_inline_kb

        case 'translations':
            translations_language = state_data.get('translations_language')
            answer_text = (
                f'<b>Язык:</b> {language_name}\n'
                f'<b>Слово:</b> {word_text}\n\n'
                f'<b>{additions_field_pretty_name}:</b> {len(additions_data)} \n\n'
                f'{additions_field_description} \n\n'
                f'<b>Текущий язык переводов:</b> {translations_language} \n\n'
                f'Нажмите Вернуться назад, чтобы вернуться к слову.'
            )
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text='Сменить язык переводов',
                            callback_data='customizing_change_translations_language',
                        ),
                    ],
                    [
                        return_button,
                    ],
                ]
            )

        case 'note':
            answer_text = (
                f'<b>Язык:</b> {language_name}\n'
                f'<b>Слово:</b> {word_text}\n\n'
                f'<b>{additions_field_pretty_name}:</b> <i>Нет заметки</i> \n\n'
                f'{additions_field_description} \n\n'
                f'Нажмите Вернуться назад, чтобы вернуться к слову.'
            )
            markup = return_inline_kb

        case _:
            answer_text = (
                f'<b>Язык:</b> {language_name}\n'
                f'<b>Слово:</b> {word_text}\n\n'
                f'<b>{additions_field_pretty_name}:</b> {len(additions_data)} \n\n'
                f'{additions_field_description} \n\n'
                f'Нажмите Вернуться назад, чтобы вернуться к слову.'
            )
            markup = return_inline_kb

    if additions_data:
        markup = await generate_word_customization_markup(
            additions_field, additions_data
        )

        if additions_field == 'image_associations':
            images_ids = [image_id for image_id, _ in additions_data]
            images = [InputMediaPhoto(media=image_id) for image_id in images_ids]
            await message.answer_media_group(images)

        if additions_field == 'note':
            answer_text = (
                f'<b>Язык:</b> {language_name}\n'
                f'<b>Слово:</b> {word_text}\n\n'
                f'<b>{additions_field_pretty_name}:</b> {additions_data} \n\n'
                f'{additions_field_description} \n\n'
                f'Нажмите Вернуться назад, чтобы вернуться к слову.'
            )

    await message.answer(
        answer_text,
        reply_markup=markup,
    )


@router.callback_query(F.data.startswith('customizing_clear_image_associations'))
async def customizing_clear_image_associations_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Removes all word images from state."""
    await state.update_data(image_associations=[], image_associations_count=0)
    await word_create_customization_callback(callback_query.message, state)


@router.callback_query(F.data.startswith('customizing_change_translations_language'))
async def customizing_change_translations_language_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Sends languages to choose for translations language."""
    await callback_query.answer('Сменить язык переводов')

    state_data = await state.get_data()

    # generate inline keyboard
    learning_languages_info: list = list(state_data.get('learning_languages_info'))
    native_languages_info: list = state_data.get('native_languages_info')
    all_languages_info = set(learning_languages_info + native_languages_info)

    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.add(
        *[
            InlineKeyboardButton(
                text=language_name,
                callback_data=f'translations_language_{language_name}',
            )
            for language_name in all_languages_info
        ]
    )
    keyboard_builder.adjust(LEARNING_LANGUAGES_MARKUP_SIZE)
    keyboard_builder.row(cancel_button)
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())

    await callback_query.message.answer(
        'Выберите язык:',
        reply_markup=markup,
    )


@router.callback_query(F.data.startswith('translations_language'))
async def translations_language_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Updates state data with chosen translations language."""
    language_name = callback_query.data.split('_')[-1]
    await callback_query.answer(language_name)
    await state.update_data(translations_language=language_name)
    await word_create_customization_callback(callback_query.message, state)


@router.message(WordCreate.customizing_value)
async def word_create_customizing_proceed(message: Message, state: FSMContext):
    """Updates additions state data with new values, sends updated info."""
    customizing_value = message.text

    state_data = await state.get_data()
    additions_field = state_data.get('current_customizing_field')
    additions_data = state_data.get(additions_field)
    additions_data = additions_data if additions_data else []

    match additions_field:
        case (
            'translations'
            | 'examples'
            | 'definitions'
            | 'synonyms'
            | 'antonyms'
            | 'forms'
            | 'similars'
            | 'collections'
        ):
            split_symbols = [';', '; ']

        case 'types' | 'tags':
            split_symbols = [',', ' ', ', ']

        case 'form_groups':
            split_symbols = [',', ', ']

        case 'image_associations':
            try:
                image_file_id = message.photo[-1].file_id
                file_in_io = io.BytesIO()
                await message.bot.download(file=image_file_id, destination=file_in_io)
                encoded_image = base64.b64encode(file_in_io.getvalue()).decode('utf-8')
                additions_data.append((image_file_id, encoded_image))

                await state.update_data(
                    **{
                        additions_field: additions_data,
                        f'{additions_field}_count': len(additions_data),
                    }
                )
                state_data = await state.get_data()

            except TypeError:
                pass

            await word_create_customization_callback(message, state)
            return None

        case 'note':
            await state.update_data(
                **{
                    additions_field: message.text,
                    f'{additions_field}_count': 1,
                }
            )
            await word_create_customization_callback(message, state)
            return None

        case _:
            raise AssertionError('Word create: Unknown customization field was passed')

    new_values = None
    for symb in split_symbols:
        match customizing_value.find(symb):
            case -1:
                continue
            case _:
                new_values = customizing_value.split(symb)

    # convert to expected type if no split symbols were found
    if new_values is None:
        new_values = [customizing_value]

    if additions_field == 'translations':
        translations_language = state_data.get('translations_language')
        new_values = [(translations_language, new_value) for new_value in new_values]

    additions_data.extend(new_values)
    await state.update_data(
        **{
            additions_field: additions_data,
            f'{additions_field}_count': len(additions_data),
        }
    )
    state_data = await state.get_data()

    await word_create_customization_callback(message, state)


@router.callback_query(F.data.startswith('customizing_edit'))
async def word_create_customizing_edit_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Sends chosen additions object state data, include delete button, sets state that awaits new value to update object."""
    customizing_edit_index = int(callback_query.data.split('_')[-1])
    await state.update_data(
        customizing_edit_index=customizing_edit_index,
        previous_state_handler=word_create_customization_callback,
    )

    await state.set_state(WordCreate.customizing_edit_value)

    state_data = await state.get_data()
    additions_field = state_data.get('current_customizing_field')
    additions_data: list = state_data.get(additions_field)
    customizing_current_value = additions_data[customizing_edit_index]

    await callback_query.answer(f'Редактирование: {customizing_current_value}')

    await callback_query.message.answer(
        (
            f'Редактировать: {customizing_current_value} \n\n'
            f'Введите новое значение или нажмите Удалить для удаления значения.'
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Удалить', callback_data='customizing_delete'
                    ),
                ],
                [
                    return_button,
                ],
            ]
        ),
    )


@router.message(WordCreate.customizing_edit_value)
async def word_create_customizing_edit_proceed(message: Message, state: FSMContext):
    """Updates chosen additions object state data with passed value."""
    state_data = await state.get_data()
    additions_field = state_data.get('current_customizing_field')
    additions_data: list = state_data.get(additions_field)
    customizing_edit_index = state_data.get('customizing_edit_index')
    additions_data.pop(customizing_edit_index)
    new_value = message.text

    match additions_field:
        case 'translations':
            translations_language = state_data.get('translations_language')
            new_value = (translations_language, new_value)
        case _:
            pass

    additions_data.insert(customizing_edit_index, new_value)
    await state.update_data({additions_field: additions_data})

    await word_create_customization_callback(message, state)


@router.callback_query(F.data.startswith('customizing_delete'))
async def word_create_customizing_delete_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Removes chosen additions object from state data."""
    state_data = await state.get_data()
    additions_field = state_data.get('current_customizing_field')
    additions_data: list = state_data.get(additions_field)
    customizing_edit_index = state_data.get('customizing_edit_index')
    customizing_current_value = additions_data.pop(customizing_edit_index)

    await callback_query.answer(f'Удаление: {customizing_current_value}')

    await state.update_data({additions_field: additions_data})
    await state.update_data({f'{additions_field}_count': len(additions_data)})

    await word_create_customization_callback(callback_query.message, state)


@router.callback_query(F.data.startswith('save_word'))
async def word_create_save_callback(
    callback_query: CallbackQuery,
    state: FSMContext,
    request_data: dict = {},
    *args,
    **kwargs,
) -> None:
    """Makes API request to create or update word, generates request data from state data, sends new or updated word profile info."""
    await state.update_data(word_create_handler=word_create_save_callback)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)

    await callback_query.answer('Сохранение...')

    if not request_data:
        request_data = await generate_word_create_request_data(state_data)
        await state.update_data(request_data=request_data)

    url = (
        state_data.get('url')
        if VOCABULARY_URL in state_data.get('url')
        else VOCABULARY_URL
    )
    method = state_data.get('method')

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method=method, data=request_data)
        async with session.__getattribute__(method)(
            url=url, json=request_data, headers=headers
        ) as response:
            match response.status:
                case HTTPStatus.OK | HTTPStatus.CREATED:
                    response_data: dict = await response.json()
                    word_text = response_data.get('text')
                    word_slug = response_data.get('slug')

                    await state.set_state(WordProfile.retrieve)
                    await state.update_data(
                        previous_state_handler=vocabulary_choose_language_callback,
                        response_data=response_data,
                        word_text=word_text,
                        word_slug=word_slug,
                        vocabulary_send_request=True,
                    )

                    await callback_query.message.answer(
                        f'Открываю профиль слова {word_text}...',
                        reply_markup=word_profile_kb,
                    )

                    await send_word_profile_answer(
                        callback_query.message,
                        state,
                        state_data,
                        response_data,
                        session,
                        headers,
                    )

                    # update learning languages in state info in case new language was passed within new word
                    await save_learning_languages_to_state(
                        callback_query.message, state, session, headers
                    )

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(callback_query.message, state)

                case HTTPStatus.BAD_REQUEST:
                    await send_validation_errors(
                        callback_query.message, state, response
                    )

                case HTTPStatus.CONFLICT:
                    await send_conflicts_errors(callback_query.message, state, response)

                case _:
                    await send_error_message(callback_query.message, state, response)


@router.callback_query(F.data.startswith('word_create_existing_word'))
async def word_create_update_existing_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Updates word instead of create if word already exists."""
    await callback_query.answer('Сохранение...')
    state_data = await state.get_data()
    request_data = state_data.get('request_data')
    existing_word_id = state_data.get('existing_word_id')
    existing_word_data = state_data.get('existing_word_data')
    mode = callback_query.data.split('__')[-1]

    try:
        word_index = int(state_data.get('conflict_object_index'))
        match mode:
            case 'update':
                request_data['words'][word_index]['id'] = existing_word_id
            case 'get':
                request_data['words'][word_index] = existing_word_data

    except (KeyError, AttributeError, TypeError):
        match mode:
            case 'update':
                request_data['id'] = existing_word_id
            case 'get':
                request_data = existing_word_data

    await state.update_data(request_data=request_data)

    word_create_handler = state_data.get('word_create_handler')
    await word_create_handler(callback_query, state, request_data=request_data)


@router.callback_query(F.data.startswith('word_create_existing_nested'))
async def word_create_update_existing_nested_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Updates word nested object instead of create if object already exists."""
    await callback_query.answer('Сохранение...')
    state_data = await state.get_data()
    request_data = state_data.get('request_data')
    conflict_nested_field = state_data.get('conflict_nested_field')
    existing_nested_object_id = state_data.get('existing_nested_object_id')
    existing_nested_object_data = state_data.get('existing_nested_object_data')
    mode = callback_query.data.split('__')[-1]
    word_self_related_field = None
    if len(callback_query.data.split('__')) == 3:
        word_self_related_field = callback_query.data.split('__')[-2]

    try:
        conflict_field = state_data.get('conflict_field')
        conflict_object_index = state_data.get('conflict_object_index')

        object_data: dict = request_data[conflict_field][conflict_object_index]
        nested_objects_data: list[dict] = object_data[conflict_nested_field]
        new_nested_object_data: str = state_data.get('new_nested_object_data')
        try:
            nested_object_index: int = nested_objects_data.index(new_nested_object_data)
        except ValueError:
            nested_object_index: int = nested_objects_data.index(
                {word_self_related_field: new_nested_object_data}
            )

        match mode:
            case 'update' if word_self_related_field:
                request_data[conflict_field][conflict_object_index][
                    conflict_nested_field
                ][nested_object_index][word_self_related_field][
                    'id'
                ] = existing_nested_object_id
            case 'update':
                request_data[conflict_field][conflict_object_index][
                    conflict_nested_field
                ][nested_object_index]['id'] = existing_nested_object_id
            case 'get' if word_self_related_field:
                request_data[conflict_field][conflict_object_index][
                    conflict_nested_field
                ][nested_object_index][
                    word_self_related_field
                ] = existing_nested_object_data
            case 'get':
                request_data[conflict_field][conflict_object_index][
                    conflict_nested_field
                ][nested_object_index] = existing_nested_object_data

    except (KeyError, AttributeError, TypeError):
        nested_objects_data: list = request_data[conflict_nested_field]
        new_nested_object_data: str = state_data.get('new_nested_object_data')
        try:
            nested_object_index: int = nested_objects_data.index(new_nested_object_data)
        except ValueError:
            nested_object_index: int = nested_objects_data.index(
                {word_self_related_field: new_nested_object_data}
            )

        match mode:
            case 'update' if word_self_related_field:
                request_data[conflict_nested_field][nested_object_index][
                    word_self_related_field
                ]['id'] = existing_nested_object_id
            case 'update':
                request_data[conflict_nested_field][nested_object_index][
                    'id'
                ] = existing_nested_object_id
            case 'get' if word_self_related_field:
                request_data[conflict_nested_field][nested_object_index][
                    word_self_related_field
                ] = existing_nested_object_data
            case 'get':
                request_data[conflict_nested_field][
                    nested_object_index
                ] = existing_nested_object_data

    await state.update_data(request_data=request_data)

    word_create_handler = state_data.get('word_create_handler')
    await word_create_handler(callback_query, state, request_data=request_data)


@router.message(F.text == 'Добавить несколько новых слов')
async def word_create_multiple(message: Message, state: FSMContext) -> None:
    """Words multiple create start, sets state that awaits words language or words if language name already in state data."""
    url = VOCABULARY_URL + 'multiple-create/'
    method = 'post'
    await state.update_data(
        previous_state_handler=vocabulary_choose_language_callback,
        several_words=[],
        url=url,
        method=method,
        page_num=1,
    )

    await state.set_state(WordCreate.language_multiple)

    state_data = await state.get_data()
    language_name = state_data.get('language_choose')

    if language_name:
        await state.update_data(language=language_name)
        await state.set_state(WordCreate.several_words)
        await message.answer(
            (
                f'<b>Язык:</b> {language_name}\n\n'
                f'Введите слова или фразы, разделяя их знаком ;'
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text='Сменить язык',
                            callback_data='word_create_multiple_change_language',
                        ),
                    ],
                    [
                        cancel_button,
                    ],
                ]
            ),
        )
    else:
        # generate inline keyboard
        markup = await generate_learning_languages_markup(
            state, callback_data='word_create_multiple_language'
        )
        await message.answer(
            'Введите язык новых слов или выберите изучаемый язык:',
            reply_markup=markup,
        )

    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)

    async with aiohttp.ClientSession() as session:
        await save_native_languages_to_state(message, state, session, headers)
        await save_types_info_to_state(message, state, session, headers)


@router.callback_query(F.data.startswith('word_create_multiple_change_language'))
async def word_create_multiple_change_language_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Sets state that awaits language name for multiple create."""
    await callback_query.answer('Сменить язык')

    await state.set_state(WordCreate.language_multiple)

    # generate inline keyboard
    markup = await generate_learning_languages_markup(
        state, callback_data='word_create_multiple_language'
    )
    await callback_query.message.answer(
        'Введите язык новых слов или выберите изучаемый язык:',
        reply_markup=markup,
    )


@router.message(WordCreate.language_multiple)
@router.callback_query(F.data.startswith('word_create_multiple_language'))
async def word_create_multiple_language_proceed(
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
    await state.set_state(WordCreate.several_words)

    await message.answer(
        (
            f'<b>Язык:</b> {language_name}\n\n'
            f'Введите слова или фразы, разделяя их знаком ;'
        ),
        reply_markup=cancel_inline_kb,
    )


@router.message(WordCreate.several_words)
async def word_create_multiple_words_proceed(
    message: Message | CallbackQuery, state: FSMContext
):
    """Accepts words, sends words for customizing."""
    await state.update_data(
        previous_state_handler=vocabulary_choose_language_callback,
        pagination_handler=word_create_multiple_words_proceed,
    )

    state_data = await state.get_data()
    language_name = state_data.get('language')
    several_words = (
        state_data.get('several_words') if state_data.get('several_words') else {}
    )

    state_type = await state.get_state()

    if isinstance(message, Message) and state_type == WordCreate.several_words:
        # handle passed words
        several_words_value = message.text
        split_symbols = [';', '; ']

        new_words = None
        for symb in split_symbols:
            match several_words_value.find(symb):
                case -1:
                    continue
                case _:
                    new_words = several_words_value.split(symb)

        # convert to expected type if no split symbols were found
        if new_words is None:
            new_words = [several_words_value]

        # check words amount limit
        if len(several_words) + len(new_words) > MULTIPLE_WORDS_CREATE_AMOUNT_LIMIT:
            await message.answer(
                f'Вы превысили количество новых слов за раз: {MULTIPLE_WORDS_CREATE_AMOUNT_LIMIT} \nПожалуйста, уменьшите количество слов и повторите попытку.',
                reply_markup=cancel_inline_kb,
            )
            return None

        # generate empty data for new words
        for word in new_words:
            word_data = several_words.get(word, None)
            if word_data is None:
                several_words[word] = {}
                for additions_field in additions_pretty:
                    several_words[word][additions_field] = []
                    several_words[word][f'{additions_field}_count'] = 0

        # update state data
        several_words_paginated = await paginate_values_list(
            list(several_words), VOCABULARY_WORDS_PER_PAGE
        )
        await state.update_data(
            several_words=several_words,
            several_words_paginated=several_words_paginated,
        )
        state_data = await state.get_data()

    elif isinstance(message, CallbackQuery):
        several_words_paginated = state_data.get('several_words_paginated')
        message = message.message

    else:
        several_words_paginated = state_data.get('several_words_paginated')

    await state.set_state(WordCreate.several_words)

    # paginated words inline
    await state.update_data(pages_total_amount=len(several_words_paginated))
    words_inline_kb = await generate_words_multiple_create_markup(
        state, several_words, several_words_paginated
    )

    await message.answer(
        (
            f'<b>Язык:</b> {language_name}\n'
            f'<b>Слова:</b> {len(several_words)}\n\n'
            f'Кастомизируйте слова или нажмите Сохранить для завершения создания. \n\n'
            f'Введите еще слова, чтобы добавить их к списку введенных раннее. '
        ),
        reply_markup=words_inline_kb,
    )


@router.callback_query(F.data.startswith('word_create_multiple_edit'))
async def word_create_multiple_edit_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Chosen word customization."""
    word_index = int(callback_query.data.split('__')[-1])

    state_data = await state.get_data()
    several_words = state_data.get('several_words')
    word_text = list(several_words)[word_index]

    await callback_query.answer(word_text)

    await state.update_data(
        {
            'text': word_text,
            'word_edit_index': int(word_index),
            **several_words[word_text],
            'control_buttons': [
                InlineKeyboardButton(
                    text='Удалить', callback_data='word_create_multiple_delete'
                ),
                InlineKeyboardButton(
                    text='Вернуться назад', callback_data='word_create_multiple_return'
                ),
            ],
        }
    )

    await word_create_text_proceed(callback_query, state)


@router.callback_query(F.data.startswith('word_create_multiple_return'))
async def word_create_multiple_return_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Return to words list after single word customization."""
    state_data = await state.get_data()
    word_edit_index = state_data.get('word_edit_index')
    word_text = state_data.get('text')
    several_words: dict = state_data.get('several_words')

    # update words state data
    several_words_updated = {}
    for word_index, word_info in enumerate(several_words.items()):
        if word_index == word_edit_index:
            several_words_updated[word_text] = {}
            for additions_field in additions_pretty:
                several_words_updated[word_text][additions_field] = state_data.get(
                    additions_field
                )
                several_words_updated[word_text][
                    f'{additions_field}_count'
                ] = state_data.get(f'{additions_field}_count')
            continue
        several_words_updated[word_info[0]] = word_info[1]

    # paginate words
    several_words_paginated = await paginate_values_list(
        list(several_words_updated), VOCABULARY_WORDS_PER_PAGE
    )

    await callback_query.answer('Вернуться назад')
    await state.update_data(
        several_words=several_words_updated,
        several_words_paginated=several_words_paginated,
    )
    await word_create_multiple_words_proceed(callback_query, state)


@router.callback_query(F.data.startswith('word_create_multiple_delete'))
async def word_create_multiple_delete_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Deletes single word from new words list."""
    state_data = await state.get_data()
    word_text = state_data.get('text')
    several_words: dict = state_data.get('several_words')
    several_words.pop(word_text)
    several_words_paginated = await paginate_values_list(
        list(several_words), VOCABULARY_WORDS_PER_PAGE
    )
    await callback_query.answer('Удаление')
    await state.update_data(
        several_words=several_words, several_words_paginated=several_words_paginated
    )
    await word_create_multiple_words_proceed(callback_query, state)


@router.callback_query(F.data.startswith('multiple_save'))
async def word_create_multiple_save_callback(
    callback_query: CallbackQuery | Message,
    state: FSMContext,
    collections: list = [],
    request_data: dict = {},
) -> None:
    """Makes API request to create words list, sends updated vocabulary from response data."""
    await state.update_data(word_create_handler=word_create_multiple_save_callback)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = await get_authentication_headers(token=token)
    several_words: dict = state_data.get('several_words')
    language_name = state_data.get('language')

    if isinstance(callback_query, CallbackQuery):
        await callback_query.answer('Сохранение...')
        message: Message = callback_query.message
    else:
        message: Message = callback_query

    if not request_data:
        request_data = {'words': [], 'collections': collections}
        for word_text, word_data in several_words.items():
            request_data['words'].append(
                await generate_word_create_request_data(
                    word_data, word_text=word_text, word_language=language_name
                )
            )
        await state.update_data(request_data=request_data)

    url = state_data.get('url')
    method = state_data.get('method')

    async with aiohttp.ClientSession() as session:
        api_request_logging(url, headers=headers, method=method, data=request_data)
        async with session.__getattribute__(method)(
            url=url, json=request_data, headers=headers
        ) as response:
            match response.status:
                case HTTPStatus.CREATED:
                    response_data: dict = await response.json()
                    results_count = response_data['count']
                    pages_total_amount = math.ceil(
                        results_count / VOCABULARY_WORDS_PER_PAGE
                    )

                    if request_data['collections']:
                        await message.answer(
                            f'Слова добавлены в выбранные коллекции: {len(several_words)}'
                        )
                    else:
                        await message.answer(
                            f'Слова добавлены в ваш словарь: {len(several_words)}'
                        )

                    await state.update_data(
                        previous_state_handler=vocabulary_choose_language_callback,
                        response_data=response_data,
                        page_num=1,
                        pages_total_amount=pages_total_amount,
                        vocabulary_send_request=True,
                        collections_send_request=True,
                    )
                    await state.set_state(Vocabulary.list_retrieve)

                    if state_data.get('language_choose'):
                        await vocabulary_choose_language_callback(message, state)
                    else:
                        await message.answer(
                            'Открываю словарь...',
                            reply_markup=vocabulary_kb,
                        )
                        await send_vocabulary_answer(
                            message,
                            state,
                            response_data,
                        )

                    # update learning languages in state info in case new language was passed within new word
                    await save_learning_languages_to_state(
                        callback_query.message, state, session, headers
                    )

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case HTTPStatus.BAD_REQUEST:
                    response_data: dict = await response.json()
                    answer_text = ''

                    for word_index, detail_messages in enumerate(
                        response_data['words']
                    ):
                        if not detail_messages:
                            continue
                        invalid_word = list(several_words)[word_index]
                        answer_text += (
                            f'🚫 Слово: {invalid_word} \n'
                            f'Присутствуют ошибки в переданных данных: \n\n'
                        )
                        all_fields_pretty = fields_pretty | additions_pretty
                        answer_text = await generate_validation_errors_answer_text(
                            detail_messages, all_fields_pretty, answer_text=answer_text
                        )
                        answer_text += '\n\n'

                    await message.answer(answer_text)

                case HTTPStatus.CONFLICT:
                    await send_conflicts_errors(message, state, response)

                case _:
                    await send_error_message(message, state, response)


@router.callback_query(F.data == 'choose_collections')
async def word_create_multiple_choose_collections_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Sends user collection list to choose from API response data or state data."""
    await state.update_data(
        previous_state_handler=word_create_multiple_words_proceed,
        pagination_handler=word_create_multiple_choose_collections_callback,
    )

    if isinstance(callback_query, CallbackQuery):
        await callback_query.answer('Выбор коллекций')
        message: Message = callback_query.message
    else:
        message: Message = callback_query

    state_data = await state.get_data()
    collections_send_request = state_data.get('collections_send_request')

    if collections_send_request is False:
        collections_paginated = state_data.get('collections_paginated')
        collections_count = state_data.get('collections_count')
        markup = await generate_collections_markup(
            state,
            collections_paginated,
            callback_data='multiple_create_choose_collection',
        )

        if collections_count == 0:
            answer_text = (
                f'Коллекции: {collections_count} \n\n'
                f'Введите названия новых коллекций, разделяя их знаком ;'
            )
        else:
            answer_text = (
                f'Коллекции: {collections_count} \n\n'
                f'Выберите коллекцию, в которую хотите сохранить новые слова, или '
                f'введите названия нескольких коллекций, разделяя их знаком ; \n\n'
                f'Коллекции могут быть как новыми, так и уже созданными.'
            )

        await state.set_state(WordCreate.add_to_collections)

        await message.answer(answer_text, reply_markup=markup)

    else:
        token = state_data.get('token')
        headers = await get_authentication_headers(token=token)
        url = COLLECTIONS_URL

        async with aiohttp.ClientSession() as session:
            api_request_logging(url, headers=headers, method='get')
            async with session.get(url=url, headers=headers) as response:
                match response.status:
                    case HTTPStatus.OK:
                        response_data: dict = await response.json()
                        results_count = response_data['count']

                        # set pages_total_amount value
                        pages_total_amount = math.ceil(
                            results_count / COLLECTIONS_PER_PAGE
                        )
                        await state.update_data(
                            pages_total_amount=pages_total_amount, page_num=1
                        )

                        collections_paginated = (
                            await save_paginated_collections_to_state(
                                state, response_data, results_count
                            )
                        )
                        markup = await generate_collections_markup(
                            state,
                            collections_paginated,
                            callback_data='multiple_create_choose_collection',
                        )

                        if results_count == 0:
                            answer_text = (
                                f'Коллекции: {results_count} \n\n'
                                f'Введите названия новых коллекций, разделяя их знаком ;'
                            )
                        else:
                            answer_text = (
                                f'Коллекции: {results_count} \n\n'
                                f'Выберите коллекцию, в которую хотите сохранить новые слова, или '
                                f'введите названия нескольких коллекций, разделяя их знаком ; \n\n'
                                f'Коллекции могут быть как новыми, так и уже созданными.'
                            )

                        await state.set_state(WordCreate.add_to_collections)

                        await message.answer(answer_text, reply_markup=markup)

                    case HTTPStatus.UNAUTHORIZED:
                        await send_unauthorized_response(message, state)

                    case _:
                        await send_error_message(message, state, response)


@router.message(WordCreate.add_to_collections)
@router.callback_query(F.data.startswith('multiple_create_choose_collection'))
async def word_create_multiple_save_to_collections_proceed(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Makes API request with chosen collections, calls multiple words save callback."""
    state_data = await state.get_data()

    if isinstance(callback_query, CallbackQuery):
        collection_index = int(callback_query.data.split('__')[-1])
        collections_list = state_data.get('collections_list')
        collection_title = collections_list[collection_index]
        await callback_query.answer(collection_title)
        message = callback_query.message
        collections_titles = [collection_title]
    else:
        message = callback_query
        passed_collections = message.text
        split_symbols = [';', '; ']
        collections_titles = None
        for symb in split_symbols:
            match passed_collections.find(symb):
                case -1:
                    continue
                case _:
                    collections_titles = passed_collections.split(symb)

        # convert to expected type if no split symbols were found
        if collections_titles is None:
            collections_titles = [passed_collections]

    await word_create_multiple_save_callback(
        callback_query,
        state,
        collections=[
            {'title': collection_title} for collection_title in collections_titles
        ],
    )
