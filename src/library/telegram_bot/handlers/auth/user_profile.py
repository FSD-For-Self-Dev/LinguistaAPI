"""User profile handlers."""

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
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from emoji import emojize
from dotenv import load_dotenv

from keyboards.core import initial_kb, cancel_button, cancel_inline_kb
from keyboards.user_profile import profile_update_kb
from states.user_profile import (
    UserProfileUpdate,
    AddLearningLanguage,
    user_profile_retrieve,
)
from handlers.urls import (
    AVAILABLE_LANGUAGES_URL,
    LEARNING_LANGUAGES_URL,
    USER_PROFILE_URL,
    LOG_OUT_URL,
)
from handlers.utils import (
    get_authentication_headers,
    send_user_profile_answer,
    send_error_message,
    api_request_logging,
    send_unauthorized_response,
    send_validation_errors,
)


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == 'Профиль')
async def get_user_profile(message: Message, state: FSMContext) -> None:
    """Return user profile data."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    async with aiohttp.ClientSession() as session:
        api_request_logging(USER_PROFILE_URL, headers=headers)
        async with session.get(url=USER_PROFILE_URL, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data = await response.json()
                    await state.set_state(user_profile_retrieve)
                    await send_user_profile_answer(
                        session, message, state, response_data, headers=headers
                    )
                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Редактировать профиль')
async def update_user_profile(message: Message, state: FSMContext) -> None:
    """Set state, send options to choose."""
    await state.set_state(UserProfileUpdate.options)
    await state.update_data(previous_state_handler=get_user_profile)

    await message.answer(
        'Выберите данные для редактирования.',
        reply_markup=profile_update_kb,
    )


@router.message(F.text == 'Обновить фото профиля')
async def update_profile_image(message: Message, state: FSMContext) -> None:
    """Set state, wait for image file from user."""
    await state.set_state(UserProfileUpdate.profile_image)
    await state.update_data(previous_state_handler=update_user_profile)

    await message.answer(
        'Отправьте картинку для обновления фото профиля.',
        reply_markup=cancel_inline_kb,
    )


@router.message(UserProfileUpdate.profile_image)
async def update_profile_image_proceed(message: Message, state: FSMContext) -> None:
    """Recieve, download profile image file, update state data, send request to api."""

    if not message.photo:
        await message.answer(
            (
                'Ответ не содержит картинки. \n'
                'Отправьте картинку для обновления фото профиля.'
            ),
            reply_markup=cancel_inline_kb,
        )
        return None

    await state.update_data(profile_image=message.photo)

    image_file_id = message.photo[-1].file_id
    file_in_io = io.BytesIO()
    await message.bot.download(file=image_file_id, destination=file_in_io)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    encoded_image = base64.b64encode(file_in_io.getvalue()).decode('utf-8')
    request_data = {'image': encoded_image}

    async with aiohttp.ClientSession() as session:
        api_request_logging(
            USER_PROFILE_URL, data=request_data, headers=headers, method='patch'
        )
        async with session.patch(
            url=USER_PROFILE_URL, json=request_data, headers=headers
        ) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data = await response.json()
                    await message.answer(emojize('Фото профиля обновлено :sparkles:'))
                    await state.set_state(user_profile_retrieve)
                    await send_user_profile_answer(
                        session, message, state, response_data, headers=headers
                    )
                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)
                case HTTPStatus.BAD_REQUEST:
                    await send_validation_errors(message, state, response)
                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Изменить имя')
async def update_first_name(message: Message, state: FSMContext) -> None:
    """Set state, wait for message from user."""
    await state.set_state(UserProfileUpdate.first_name)
    await state.update_data(previous_state_handler=update_user_profile)

    await message.answer(
        (
            'Введите имя, оно будет отображаться в вашем профиле и будет видно другим пользователям. '
        ),
        reply_markup=cancel_inline_kb,
    )


@router.message(UserProfileUpdate.first_name)
async def update_first_name_proceed(message: Message, state: FSMContext) -> None:
    """Recieve first name, update state data, send request to api."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    await state.update_data(first_name=message.text)

    request_data = {'first_name': message.text}

    async with aiohttp.ClientSession() as session:
        api_request_logging(
            USER_PROFILE_URL, data=request_data, headers=headers, method='patch'
        )
        async with session.patch(
            url=USER_PROFILE_URL, json=request_data, headers=headers
        ) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data = await response.json()
                    await message.answer(emojize('Имя обновлено :sparkles:'))
                    await state.set_state(user_profile_retrieve)
                    await send_user_profile_answer(
                        session, message, state, response_data, headers=headers
                    )
                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)
                case HTTPStatus.BAD_REQUEST:
                    await send_validation_errors(message, state, response)
                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Изменить родные языки')
async def update_native_languages(message: Message, state: FSMContext) -> None:
    """Set state, wait for message from user."""
    await state.set_state(UserProfileUpdate.native_languages)
    await state.update_data(previous_state_handler=update_user_profile)

    await message.answer(
        (
            'Введите все родные языки через запятую или/и пробел. '
            'Пример: Русский, Английский.'
        ),
        reply_markup=cancel_inline_kb,
    )


@router.message(UserProfileUpdate.native_languages)
async def native_languages_proceed(message: Message, state: FSMContext) -> None:
    """Recieve languages, update state data, send request to api."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    languages = message.text
    await state.update_data(native_languages=languages)

    # split languages if several passed
    split_symbols = [',', ' ', ', ']
    split_languages = []
    for symb in split_symbols:
        match languages.find(symb):
            case -1:
                continue
            case _:
                split_languages = languages.split(symb)

    # convert to api expected type
    if not split_languages:
        split_languages = [languages]

    request_data = {'native_languages': split_languages}

    async with aiohttp.ClientSession() as session:
        api_request_logging(
            USER_PROFILE_URL, data=request_data, headers=headers, method='patch'
        )
        async with session.patch(
            url=USER_PROFILE_URL, json=request_data, headers=headers
        ) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data = await response.json()
                    await message.answer(emojize('Родные языки обновлены :sparkles:'))
                    await state.set_state(user_profile_retrieve)
                    await send_user_profile_answer(
                        session, message, state, response_data, headers=headers
                    )
                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)
                case HTTPStatus.BAD_REQUEST:
                    await send_validation_errors(message, state, response)
                case HTTPStatus.CONFLICT:
                    # response_data = await response.json()
                    # detail_message = response_data.get('detail')  # use error this when multilanguages will be provided (interface language switch)
                    await message.answer('Количество родных языков превышено.')
                case _:
                    await send_error_message(message, state, response)


@router.message(F.text == 'Добавить изучаемый язык')
async def add_learning_language(message: Message, state: FSMContext) -> None:
    """Set state, wait for message from user or button callback."""
    await state.set_state(AddLearningLanguage.language)
    await state.update_data(previous_state_handler=get_user_profile)

    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    # get available languages from API
    async with aiohttp.ClientSession() as session:
        api_request_logging(AVAILABLE_LANGUAGES_URL, headers=headers, method='get')
        async with session.get(
            url=AVAILABLE_LANGUAGES_URL, headers=headers
        ) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data = await response.json()
                    available_languages_names = [
                        language['name'] for language in response_data['results']
                    ]
                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)
                case _:
                    await send_error_message(message, state, response)

    # generate inline keyboard
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.add(
        *[
            InlineKeyboardButton(
                text=language_name, callback_data=f'add_language_{language_name}'
            )
            for language_name in available_languages_names
        ]
    )
    keyboard_builder.adjust(4)
    keyboard_builder.row(cancel_button)
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())

    await message.answer(
        ('Введите или выберите язык из списка: '),
        reply_markup=markup,
    )


async def add_learning_language_query(
    message: Message, state: FSMContext, language_name: str
) -> None:
    """Update state data, send request to api."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    await state.update_data(language=language_name)

    request_data = [{'language': language_name}]

    async with aiohttp.ClientSession() as session:
        api_request_logging(
            LEARNING_LANGUAGES_URL, data=request_data, headers=headers, method='post'
        )
        async with session.post(
            url=LEARNING_LANGUAGES_URL, json=request_data, headers=headers
        ) as response:
            match response.status:
                case HTTPStatus.CREATED:
                    response_data = await response.json()
                    await message.answer(
                        emojize('Язык добавлен в изучаемые :sparkles:')
                    )
                    # get updated user profile
                    async with session.get(
                        url=USER_PROFILE_URL, headers=headers
                    ) as response:
                        match response.status:
                            case HTTPStatus.OK:
                                response_data = await response.json()
                                await state.set_state(user_profile_retrieve)
                                await send_user_profile_answer(
                                    session,
                                    message,
                                    state,
                                    response_data,
                                    headers=headers,
                                )
                            case _:
                                await send_error_message(message, state, response)
                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)
                case HTTPStatus.BAD_REQUEST:
                    await send_validation_errors(message, state, response)
                case HTTPStatus.CONFLICT:
                    # response_data = await response.json()
                    # detail_message = response_data.get('detail')  # use error this when multilanguages will be provided (interface language switch)
                    await message.answer('Количество изучаемых языков превышено.')
                case _:
                    await send_error_message(message, state, response)


@router.callback_query(F.data.startswith('add_language'))
async def process_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Recieve language from button callback."""
    language_name = callback_query.data.split('_')[-1]
    await callback_query.answer(f'Выбран язык: {language_name}')
    await add_learning_language_query(callback_query.message, state, language_name)


@router.message(AddLearningLanguage.language)
async def add_learning_language_proceed(message: Message, state: FSMContext) -> None:
    """Recieve language from message text."""
    language_name = message.text
    await add_learning_language_query(message, state, language_name)


@router.message(F.text == 'Выйти из аккаунта')
async def logout(message: Message, state: FSMContext) -> None:
    """Clear state, send logout api request."""
    state_data = await state.get_data()
    token = state_data.get('token')
    headers = get_authentication_headers(token=token)

    await state.clear()

    async with aiohttp.ClientSession() as session:
        api_request_logging(LOG_OUT_URL, headers=headers, method='post')
        async with session.post(url=LOG_OUT_URL, headers=headers) as response:
            match response.status:
                case HTTPStatus.OK:
                    await message.answer(
                        emojize(
                            'Вы вышли из аккаунта Лингвисты, будем ждать вас снова! 👾'
                        ),
                        reply_markup=initial_kb,
                    )
                case HTTPStatus.UNAUTHORIZED:
                    await send_unauthorized_response(message, state)
                case _:
                    await send_error_message(message, state, response)
