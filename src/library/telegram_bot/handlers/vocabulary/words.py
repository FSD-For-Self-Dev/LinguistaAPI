"""Words CRUD handlres."""

import os
import logging
from http import HTTPStatus
import io
import base64

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
from keyboards.vocabulary import word_profile_kb
from states.vocabulary import WordProfile, WordCreate
from handlers.urls import VOCABULARY_URL, TYPES_URL, NATIVE_LANGUAGES_URL
from handlers.utils import (
    send_error_message,
    api_request_logging,
    get_authentication_headers,
    send_unauthorized_response,
    send_validation_errors,
    send_conflicts_errors,
)

from .vocabulary import vocabulary_choose_language_callback
from .constants import LEARNING_LANGUAGES_MARKUP_SIZE, additionals_pretty


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

router = Router()


def generate_word_profile_markup(
    state_data: dict, response_data: dict
) -> InlineKeyboardMarkup:
    """Returns markup that contains word profile info."""
    translations_count = response_data.get('translations_count')
    examples_count = response_data.get('examples_count')
    definitions_count = response_data.get('definitions_count')
    image_associations_count = response_data.get('images_count')
    synonyms_count = response_data.get('synonyms_count')
    antonyms_count = response_data.get('antonyms_count')
    forms_count = response_data.get('forms_count')
    similars_count = response_data.get('similars_count')
    collections_count = response_data.get('collections_count')

    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.add(
        InlineKeyboardButton(
            text=f'Переводы {translations_count}',
            callback_data='additions_profile__translations',
        ),
        InlineKeyboardButton(
            text=f'Примеры {examples_count}',
            callback_data='additions_profile__examples',
        ),
        InlineKeyboardButton(
            text=f'Определения {definitions_count}',
            callback_data='additions_profile__definitions',
        ),
        InlineKeyboardButton(
            text=f'Картинки-ассоциации {image_associations_count}',
            callback_data='additions_profile__images',
        ),
        InlineKeyboardButton(
            text=f'Синонимы {synonyms_count}',
            callback_data='additions_profile__synonyms',
        ),
        InlineKeyboardButton(
            text=f'Антонимы {antonyms_count}',
            callback_data='additions_profile__antonyms',
        ),
        InlineKeyboardButton(
            text=f'Формы {forms_count}', callback_data='additions_profile__forms'
        ),
        InlineKeyboardButton(
            text=f'Похожие слова {similars_count}',
            callback_data='additions_profile__similars',
        ),
        InlineKeyboardButton(
            text=f'Коллекции {collections_count}',
            callback_data='additions_profile__collections',
        ),
    )

    keyboard_builder.adjust(3)

    favorite = response_data['favorite']
    if favorite:
        keyboard_builder.row(
            InlineKeyboardButton(
                text='Удалить из избранного', callback_data='word_favorite__delete'
            )
        )
    else:
        keyboard_builder.row(
            InlineKeyboardButton(
                text='Добавить в избранное', callback_data='word_favorite__post'
            )
        )

    is_problematic = response_data['is_problematic']
    if is_problematic:
        keyboard_builder.row(
            InlineKeyboardButton(
                text='Удалить из проблемных', callback_data='problematic_toggle__delete'
            )
        )
    else:
        keyboard_builder.row(
            InlineKeyboardButton(
                text='Отметить проблемным', callback_data='problematic_toggle__post'
            )
        )

    keyboard_builder.row(
        InlineKeyboardButton(text='Вернуться назад', callback_data='cancel')
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())


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


async def send_word_profile_answer(
    message: Message,
    state: FSMContext,
    state_data: dict,
    response_data: dict,
    session: aiohttp.ClientSession,
    headers: dict,
) -> None:
    """Sends word profile."""
    # generate answer text
    answer_text = generate_word_profile_answer_text(state_data, response_data)
    await state.update_data(answer_text=answer_text)

    # generate markup
    markup = generate_word_profile_markup(state_data, response_data)

    try:
        images_data = state_data.get('images')
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
            last_image_url = response_data['images'][0]
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

            images_data = state_data.get('images')
            images_data = images_data if images_data else {}
            word_slug = state_data.get('word_slug')
            images_data[word_slug] = msg.photo[-1].file_id
            await state.update_data(images=images_data)

        except IndexError:
            # send only text
            await message.answer(answer_text, reply_markup=markup)


@router.callback_query(F.data.startswith('word_profile'))
async def word_profile_callback(
    callback_query: CallbackQuery | Message, state: FSMContext, *args, **kwargs
) -> None:
    """Sets retrieve word profile state, makes API request to get word info, sends word profile info."""
    await state.update_data(previous_state_handler=vocabulary_choose_language_callback)

    await state.set_state(WordProfile.retrieve)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    if isinstance(callback_query, CallbackQuery):
        message: Message = callback_query.message

        word_slug = callback_query.data.split('__')[-1]
        word_text = callback_query.data.split('__')[-2]

        await callback_query.answer(f'Выбрано слово: {word_text}')
        await state.update_data(word_slug=word_slug)
        await state.update_data(word_text=word_text)
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
    await state.update_data(previous_state_handler=word_profile_callback)

    message: Message = callback_query.message
    method = callback_query.data.split('__')[-1]

    match method:
        case 'post':
            await callback_query.answer('Добавить в избранное')
            await message.answer('Добавление в избранное...')
        case 'delete':
            await callback_query.answer('Удалить из избранного')
            await message.answer('Удаление из избранного...')

    state_data = await state.get_data()
    word_slug = state_data.get('word_slug')
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

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
            await callback_query.answer('Отметить проблемным')
            await message.answer('Добавление в проблемные...')
        case 'delete':
            await callback_query.answer('Удалить из проблемных')
            await message.answer('Удаление из проблемных...')

    state_data = await state.get_data()
    word_slug = state_data.get('word_slug')
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

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
                    await send_unauthorized_response(callback_query.message, state)

                case _:
                    await send_error_message(callback_query.message, state, response)


async def fill_state_data_with_response_data(
    state: FSMContext, word_profile_response_data: dict
) -> None:
    """Fills word state data in expected format with word profile response data."""
    fields_to_fill = (
        list(additionals_pretty)
        + [f'{additionals_field}_count' for additionals_field in additionals_pretty]
        + ['language', 'text']
    )

    for field in fields_to_fill:
        match field:
            case (
                'examples'
                | 'definitions'
                | 'synonyms'
                | 'antonyms'
                | 'forms'
                | 'similars'
            ):
                field_data = [
                    data['text'] for data in word_profile_response_data[field]
                ]

            case 'form_groups' | 'tags':
                field_data = [
                    data['name'] for data in word_profile_response_data[field]
                ]

            case 'collections':
                field_data = [
                    data['title'] for data in word_profile_response_data[field]
                ]

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


async def update_state_with_native_languages_info(
    message: Message, state: FSMContext, session: aiohttp.ClientSession, headers: dict
) -> None:
    """Makes API request to user native languages endpoint, saves response data to state."""
    url = TYPES_URL
    api_request_logging(url, headers=headers, method='get')
    async with session.get(url=url, headers=headers) as response:
        match response.status:
            case HTTPStatus.OK:
                response_data: dict = await response.json()
                types_available = [word_type['name'] for word_type in response_data]
                await state.update_data(types_available=types_available)
            case HTTPStatus.UNAUTHORIZED:
                await send_unauthorized_response(message, state)
                return None
            case _:
                await send_error_message(message, state, response)
                return None


async def update_state_with_types_info(
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
                await state.update_data(translations_language=native_languages_info[-1])

            case HTTPStatus.UNAUTHORIZED:
                await send_unauthorized_response(message, state)
                return None
            case _:
                await send_error_message(message, state, response)
                return None


@router.message(F.text == 'Редактировать', WordProfile.retrieve)
async def word_update(message: Message, state: FSMContext) -> None:
    """Sets update word state, calls word create handler with current word data."""
    await state.update_data(previous_state_handler=word_profile_callback)

    state_data = await state.get_data()
    profile_response_data = state_data.get('response_data')
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    await state.set_state(WordCreate.update)

    async with aiohttp.ClientSession() as session:
        await update_state_with_native_languages_info(message, state, session, headers)
        await update_state_with_types_info(message, state, session, headers)

    await fill_state_data_with_response_data(state, profile_response_data)

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
    headers = get_authentication_headers(token=token)
    url = state_data.get('url')

    await callback_query.answer('Удалить')

    async with aiohttp.ClientSession() as session:
        message = callback_query.message
        api_request_logging(url, headers=headers, method='delete')
        async with session.delete(url=url, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK | HTTPStatus.NO_CONTENT:
                    await message.answer('Слово удалено из вашего словаря.')
                    # await state.set_state(Vocabulary.retrieve)
                    await vocabulary_choose_language_callback(message, state)

                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)

                case _:
                    await send_error_message(message, state, response)


def generate_learning_languages_from_state_inline_kb(
    state_data: dict
) -> InlineKeyboardMarkup:
    """Returns inline keyboard with learning languages names from state data."""
    learning_languages_info: dict = state_data.get('learning_languages_info')
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.add(
        *[
            InlineKeyboardButton(
                text=language_name,
                callback_data=f'word_create_language_{language_name}',
            )
            for language_name in learning_languages_info.keys()
        ]
    )
    keyboard_builder.adjust(LEARNING_LANGUAGES_MARKUP_SIZE)
    keyboard_builder.row(cancel_button)
    return InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())


@router.message(F.text == 'Добавить новое слово')
async def word_create(message: Message, state: FSMContext) -> None:
    """Sets state that awaits for language name or text, if language name already defined."""
    await state.update_data(
        previous_state_handler=vocabulary_choose_language_callback,
        create_start=True,
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
        markup = generate_learning_languages_from_state_inline_kb(state_data)
        await message.answer(
            'Введите язык нового слова или выберите изучаемый язык:',
            reply_markup=markup,
        )

    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    async with aiohttp.ClientSession() as session:
        await update_state_with_native_languages_info(message, state, session, headers)
        await update_state_with_types_info(message, state, session, headers)


@router.callback_query(F.data.startswith('word_create_change_language'))
async def word_create_change_language_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Sets state that awaits language name."""
    await callback_query.answer('Сменить язык')

    await state.set_state(WordCreate.language)

    state_data = await state.get_data()

    # generate inline keyboard
    markup = generate_learning_languages_from_state_inline_kb(state_data)
    await callback_query.message.answer(
        'Введите язык нового слова или выберите изучаемый язык:',
        reply_markup=markup,
    )


@router.message(WordCreate.language)
async def word_create_language_proceed(message: Message, state: FSMContext) -> None:
    """Updates state data with passed language name from message text, sets state that awaits word text."""
    language_name = message.text

    await state.update_data(language=language_name)
    await state.set_state(WordCreate.text)

    await message.answer(
        (f'<b>Язык:</b> {language_name}\n\n' f'Введите слово или фразу.'),
        reply_markup=cancel_inline_kb,
    )


@router.callback_query(F.data.startswith('word_create_language'))
async def word_create_language_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Updates state data with passed language name from callback data, sets state that awaits word text."""
    language_name = callback_query.data.split('_')[-1]

    await callback_query.answer(language_name)

    await state.update_data(language=language_name)
    await state.set_state(WordCreate.text)

    await callback_query.message.answer(
        (f'<b>Язык:</b> {language_name}\n\n' f'Введите слово или фразу.'),
        reply_markup=cancel_inline_kb,
    )


@router.message(WordCreate.text)
async def word_create_text_proceed(message: Message | CallbackQuery, state: FSMContext):
    """Accepts word text, sets state that awaits new text, sends customization info, confirm button."""
    state_data = await state.get_data()
    language_name = state_data.get('language')
    text = state_data.get('text')
    create_start = state_data.get('create_start')

    await state.set_state(WordCreate.text_edit)

    if create_start:
        text = message.text
        await state.update_data(text=text, create_start=False)

        for additionals_field in additionals_pretty:
            await state.update_data({additionals_field: []})
            await state.update_data({f'{additionals_field}_count': 0})
            state_data = await state.get_data()

    word_customizing_inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f'Переводы {state_data.get("translations_count")}',
                    callback_data='word_customizing__translations',
                ),
                InlineKeyboardButton(
                    text=f'Примеры {state_data.get("examples_count")}',
                    callback_data='word_customizing__examples',
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f'Определения {state_data.get("definitions_count")}',
                    callback_data='word_customizing__definitions',
                ),
                InlineKeyboardButton(
                    text=f'Картинки-ассоциации {state_data.get("image_associations_count")}',
                    callback_data='word_customizing__image_associations',
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f'Синонимы {state_data.get("synonyms_count")}',
                    callback_data='word_customizing__synonyms',
                ),
                InlineKeyboardButton(
                    text=f'Антонимы {state_data.get("antonyms_count")}',
                    callback_data='word_customizing__antonyms',
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f'Формы {state_data.get("forms_count")}',
                    callback_data='word_customizing__forms',
                ),
                InlineKeyboardButton(
                    text=f'Похожие слова {state_data.get("similars_count")}',
                    callback_data='word_customizing__similars',
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f'Коллекции {state_data.get("collections_count")}',
                    callback_data='word_customizing__collections',
                ),
                InlineKeyboardButton(
                    text='Добавить заметку', callback_data='word_customizing__note'
                ),
            ],
            [
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
            ],
            [InlineKeyboardButton(text='Сохранить', callback_data='save_word')],
            [
                cancel_button,
            ],
        ]
    )

    await message.answer(
        (
            f'<b>Язык:</b> {language_name}\n'
            f'<b>Слово:</b> {text}\n\n'
            f'Кастомизируйте слово или нажмите Сохранить для завершения создания. \n\n'
            f'Введите слово еще раз, чтобы редактировать его. '
        ),
        reply_markup=word_customizing_inline_kb,
    )


@router.message(WordCreate.text_edit)
async def word_create_text_edit_proceed(
    message: Message | CallbackQuery, state: FSMContext
):
    """Updates state data with new text."""
    new_text = message.text
    await state.update_data(text=new_text)

    await word_create_text_proceed(message, state)


def generate_additionals_markup(
    additionals_field: str, additionals_data: dict
) -> InlineKeyboardMarkup:
    """Returns keyboard that contains word additionals current data with update, delete options."""
    keyboard_builder = InlineKeyboardBuilder()

    match additionals_field:
        case (
            'examples'
            | 'definitions'
            | 'synonyms'
            | 'antonyms'
            | 'forms'
            | 'similars'
            | 'types'
            | 'form_groups'
            | 'tags'
            | 'collections'
        ):
            keyboard_builder.add(
                *[
                    InlineKeyboardButton(
                        text=additional_value,
                        callback_data=f'customizing_edit_{additional_index}',
                    )
                    for additional_index, additional_value in enumerate(
                        additionals_data
                    )
                ]
            )
            keyboard_builder.adjust(2)

        case 'translations':
            keyboard_builder.add(
                *[
                    InlineKeyboardButton(
                        text=f'{additional_value[1]} ({additional_value[0]})',
                        callback_data=f'customizing_edit_{additional_index}',
                    )
                    for additional_index, additional_value in enumerate(
                        additionals_data
                    )
                ]
            )
            keyboard_builder.adjust(2)
            keyboard_builder.row(
                InlineKeyboardButton(
                    text='Сменить язык переводов',
                    callback_data='customizing_change_translations_language',
                )
            )

        case 'image_associations':
            keyboard_builder.row(
                InlineKeyboardButton(
                    text='Очистить все картинки',
                    callback_data='customizing_clear_image_associations',
                )
            )

        case 'note':
            pass

        case _:
            raise AssertionError('Word create: Unknown customization field was passed')

    keyboard_builder.row(return_button)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())


@router.callback_query(F.data.startswith('word_customizing'))
async def word_create_customization_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Returns word additionals current data with update, delete options, sets state that awaits new values."""
    await state.update_data(previous_state_handler=word_create_text_proceed)

    await state.set_state(WordCreate.customizing_value)

    state_data = await state.get_data()
    language_name = state_data.get('language')
    word_text = state_data.get('text')

    if isinstance(callback_query, CallbackQuery):
        additionals_field = callback_query.data.split('__')[-1]
        await state.update_data(current_customizing_field=additionals_field)

        (
            additionals_field_pretty_name,
            additionals_field_description,
        ) = additionals_pretty.get(additionals_field)
        await callback_query.answer(additionals_field_pretty_name)

        message: Message = callback_query.message

    else:
        additionals_field = state_data.get('current_customizing_field')
        (
            additionals_field_pretty_name,
            additionals_field_description,
        ) = additionals_pretty.get(additionals_field)

        message: Message = callback_query

    additionals_data = state_data.get(additionals_field)

    match additionals_field:
        case 'types':
            types_available = ', '.join(state_data.get('types_available'))
            answer_text = (
                f'<b>Язык:</b> {language_name}\n'
                f'<b>Слово:</b> {word_text}\n\n'
                f'<b>{additionals_field_pretty_name}:</b> {len(additionals_data)} \n\n'
                f'{additionals_field_description} \n\n'
                f'<b>Доступные типы:</b> {types_available} \n\n'
                f'Нажмите Вернуться назад, чтобы вернуться к слову.'
            )
            markup = return_inline_kb

        case 'translations':
            translations_language = state_data.get('translations_language')
            answer_text = (
                f'<b>Язык:</b> {language_name}\n'
                f'<b>Слово:</b> {word_text}\n\n'
                f'<b>{additionals_field_pretty_name}:</b> {len(additionals_data)} \n\n'
                f'{additionals_field_description} \n\n'
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
                f'<b>{additionals_field_pretty_name}:</b> <i>Нет заметки</i> \n\n'
                f'{additionals_field_description} \n\n'
                f'Нажмите Вернуться назад, чтобы вернуться к слову.'
            )
            markup = return_inline_kb

        case _:
            answer_text = (
                f'<b>Язык:</b> {language_name}\n'
                f'<b>Слово:</b> {word_text}\n\n'
                f'<b>{additionals_field_pretty_name}:</b> {len(additionals_data)} \n\n'
                f'{additionals_field_description} \n\n'
                f'Нажмите Вернуться назад, чтобы вернуться к слову.'
            )
            markup = return_inline_kb

    if additionals_data:
        markup = generate_additionals_markup(additionals_field, additionals_data)

        if additionals_field == 'image_associations':
            images_ids = [image_id for image_id, _ in additionals_data]
            images = [InputMediaPhoto(media=image_id) for image_id in images_ids]
            await message.answer_media_group(images)

        if additionals_field == 'note':
            answer_text = (
                f'<b>Язык:</b> {language_name}\n'
                f'<b>Слово:</b> {word_text}\n\n'
                f'<b>{additionals_field_pretty_name}:</b> {additionals_data} \n\n'
                f'{additionals_field_description} \n\n'
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
    """Sends translations language options."""
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
    """Updates additionals state data with new values, sends updated info."""
    customizing_value = message.text

    state_data = await state.get_data()
    additionals_field = state_data.get('current_customizing_field')
    additionals_data = state_data.get(additionals_field)
    additionals_data = additionals_data if additionals_data else []

    match additionals_field:
        case (
            'translations'
            | 'examples'
            | 'definitions'
            | 'synonyms'
            | 'antonyms'
            | 'forms'
            | 'similars'
        ):
            split_symbols = [';', '; ']

        case 'types' | 'tags':
            split_symbols = [',', ' ', ', ']

        case 'form_groups' | 'collections':
            split_symbols = [',', ', ']

        case 'image_associations':
            try:
                image_file_id = message.photo[-1].file_id
                file_in_io = io.BytesIO()
                await message.bot.download(file=image_file_id, destination=file_in_io)
                encoded_image = base64.b64encode(file_in_io.getvalue()).decode('utf-8')
                additionals_data.append((image_file_id, encoded_image))

                await state.update_data(
                    **{
                        additionals_field: additionals_data,
                        f'{additionals_field}_count': len(additionals_data),
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
                    additionals_field: message.text,
                    f'{additionals_field}_count': 1,
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
    if not new_values:
        new_values = [customizing_value]

    if additionals_field == 'translations':
        translations_language = state_data.get('translations_language')
        new_values = [(translations_language, new_value) for new_value in new_values]

    additionals_data.extend(new_values)
    await state.update_data(
        **{
            additionals_field: additionals_data,
            f'{additionals_field}_count': len(additionals_data),
        }
    )

    state_data = await state.get_data()

    await word_create_customization_callback(message, state)


@router.callback_query(F.data.startswith('customizing_edit'))
async def word_create_customizing_edit_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Sends chosen additionals object state data, include delete button, sets state that awaits new value to update object."""
    customizing_edit_index = int(callback_query.data.split('_')[-1])
    await state.update_data(
        customizing_edit_index=customizing_edit_index,
        previous_state_handler=word_create_customization_callback,
    )

    await state.set_state(WordCreate.customizing_edit_value)

    state_data = await state.get_data()
    additionals_field = state_data.get('current_customizing_field')
    additionals_data: list = state_data.get(additionals_field)
    customizing_current_value = additionals_data[customizing_edit_index]

    await callback_query.answer(f'Редактировать: {customizing_current_value}')

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
    """Updates chosen additionals object state data with passed value."""
    state_data = await state.get_data()
    additionals_field = state_data.get('current_customizing_field')
    additionals_data: list = state_data.get(additionals_field)
    customizing_edit_index = state_data.get('customizing_edit_index')
    additionals_data.pop(customizing_edit_index)
    new_value = message.text
    additionals_data.insert(customizing_edit_index, new_value)

    await state.update_data({additionals_field: additionals_data})

    await word_create_customization_callback(message, state)


@router.callback_query(F.data.startswith('customizing_delete'))
async def word_create_customizing_delete_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Removes chosen additionals object from state data."""
    state_data = await state.get_data()
    additionals_field = state_data.get('current_customizing_field')
    additionals_data: list = state_data.get(additionals_field)
    customizing_edit_index = state_data.get('customizing_edit_index')
    customizing_current_value = additionals_data.pop(customizing_edit_index)

    await callback_query.answer(f'Удалить: {customizing_current_value}')

    await state.update_data({additionals_field: additionals_data})
    await state.update_data({f'{additionals_field}_count': len(additionals_data)})

    await word_create_customization_callback(callback_query.message, state)


@router.callback_query(F.data.startswith('save_word'))
async def word_create_save_callback(
    callback_query: CallbackQuery, state: FSMContext, word_id: int | None = None
) -> None:
    """Makes API request to create or update word, generates request data from state data, sends new or updated word profile info."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    await callback_query.answer('Сохранение...')

    word_language = state_data.get('language')
    request_data = {
        'language': word_language,
        'text': state_data.get('text'),
        'note': state_data.get('note') if state_data.get('note') else '',
        'types': [word_type.capitalize() for word_type in state_data.get('types')],
        'form_groups': [
            {
                'language': word_language,
                'name': form_group,
            }
            for form_group in state_data.get('form_groups')
        ],
        'tags': [
            {
                'name': tag,
            }
            for tag in state_data.get('tags')
        ],
        'collections': [
            {
                'title': collection,
            }
            for collection in state_data.get('collections')
        ],
        'translations': [
            {
                'language': language_name,
                'text': translation,
            }
            for language_name, translation in state_data.get('translations')
        ],
        'examples': [
            {
                'language': word_language,
                'text': example,
            }
            for example in state_data.get('examples')
        ],
        'definitions': [
            {
                'language': word_language,
                'text': definition,
            }
            for definition in state_data.get('definitions')
        ],
        'image_associations': [
            {
                'image': image_b64,
            }
            for _, image_b64 in state_data.get('image_associations')
        ],
        'synonyms': [
            {
                'from_word': {
                    'language': word_language,
                    'text': synonym,
                },
            }
            for synonym in state_data.get('synonyms')
        ],
        'antonyms': [
            {
                'from_word': {
                    'language': word_language,
                    'text': antonym,
                },
            }
            for antonym in state_data.get('antonyms')
        ],
        'forms': [
            {
                'from_word': {
                    'language': word_language,
                    'text': form,
                },
            }
            for form in state_data.get('forms')
        ],
        'similars': [
            {
                'from_word': {
                    'language': word_language,
                    'text': similar,
                },
            }
            for similar in state_data.get('similars')
        ],
    }

    if word_id is not None:
        request_data['id'] = word_id

    url = state_data.get('url')
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


@router.callback_query(F.data.startswith('word_create_update_existing'))
async def word_create_update_existing_callback(
    callback_query: CallbackQuery | Message, state: FSMContext
) -> None:
    """Updates word instead of create if word already exists."""
    await callback_query.answer('Обновление')
    state_data = await state.get_data()
    word_id = state_data.get('word_existing_id')
    await word_create_save_callback(callback_query, state, word_id)
