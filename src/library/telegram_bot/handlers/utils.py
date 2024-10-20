"""Some useful utils."""

import os
import logging
import itertools

import aiohttp
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
import aiohttp.client_reqrep
from dotenv import load_dotenv

from keyboards.core import initial_kb, return_kb
from keyboards.user_profile import profile_kb


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
    """Send svalidation errors messages."""
    response_data: dict = await response.json()
    detail_messages = list(itertools.chain.from_iterable(response_data.values()))
    await message.answer('\n'.join(detail_messages))


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


def api_request_logging(url, data=None, headers=None, method='get') -> None:
    logger.debug(
        f'Sending request to API url: {url} (method: {method}, headers: {headers}, data: {data})'
    )
