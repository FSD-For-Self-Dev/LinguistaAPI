"""Authentication handlers."""

import os
import logging
import re
from http import HTTPStatus

import aiohttp
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from emoji import emojize
from dotenv import load_dotenv

from keyboards.core import cancel_inline_kb, main_kb
from states.auth import Authorization, Authorized
from handlers.urls import LOG_IN_URL
from handlers.utils import (
    send_error_message,
    api_request_logging,
    send_validation_errors,
)


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == 'Войти в аккаунт')
async def login(message: Message, state: FSMContext) -> None:
    """User authorization start, sets state that awaits username."""
    await state.set_state(Authorization.username)
    await message.answer(
        'Введите свой логин или адрес электронной почты.',
        reply_markup=cancel_inline_kb,
    )


@router.message(Authorization.username)
async def login_username_proceed(message: Message, state: FSMContext) -> None:
    """Accepts username, updates state data, sets state that awaits password."""
    # check if email or username was passed
    email_pattern = r'.+@((\w+\-+)|(\w+\.))*\w{1,63}\.[a-zA-Z]{2,6}'
    email_passed = True if re.fullmatch(email_pattern, message.text) else False
    if email_passed:
        logger.debug(f'Using email as login field: {message.text}')
        await state.update_data(email=message.text)
    else:
        logger.debug(f'Using username as login field: {message.text}')
        await state.update_data(username=message.text)

    # switch to password input
    await state.set_state(Authorization.password)
    await message.answer(
        'Введите пароль. Используйте символ || в начале и конце пароля, если хотите скрыть содержимое.',
        reply_markup=cancel_inline_kb,
    )


@router.message(Authorization.password)
async def login_password_proceed(message: Message, state: FSMContext) -> None:
    """Accepts password, makes login request to API, updates state with token."""
    await state.update_data(password=message.text)

    data = await state.get_data()

    async with aiohttp.ClientSession() as session:
        api_request_logging(LOG_IN_URL, data=data, method='post')
        async with session.post(url=LOG_IN_URL, data=data) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data: dict = await response.json()
                    token = response_data.get('key')
                    if not token:
                        logger.error(
                            'No token passed in API response data. Check authorization type.'
                        )
                    await state.clear()
                    await state.set_state(Authorized.token)
                    await state.update_data(token=token)
                    await message.answer(
                        emojize('Вход выполнен! Добро пожаловать в Лингвисту 👾'),
                        reply_markup=main_kb,
                    )
                case HTTPStatus.BAD_REQUEST:
                    await send_validation_errors(message, state, response)
                case _:
                    await send_error_message(message, state, response)
