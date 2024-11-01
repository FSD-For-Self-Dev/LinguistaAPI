"""Registration handlers."""

import os
import logging
from http import HTTPStatus

import aiohttp
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from dotenv import load_dotenv

from keyboards.core import cancel_inline_kb, initial_kb
from states.auth import Registration

from ..urls import SIGN_UP_URL
from ..utils import (
    api_request_logging,
    send_error_message,
    send_validation_errors,
)
from .authentication import login_password_proceed


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == 'Зарегистрироваться')
async def sign_up(message: Message, state: FSMContext) -> None:
    """Sign up process start, sets state that awaits username."""
    await state.set_state(Registration.username)
    await message.answer(
        'Введите уникальный логин для своего аккаунта.',
        reply_markup=cancel_inline_kb,
    )


@router.message(Registration.username)
async def sign_up_username_proceed(message: Message, state: FSMContext) -> None:
    """Accepts username, updates state data, sets state that awaits email."""
    await state.update_data(username=message.text)
    await state.set_state(Registration.email)
    await message.answer(
        'Введите адрес электронной почты, на который придет подверждение.',
        reply_markup=cancel_inline_kb,
    )


@router.message(Registration.email)
async def sign_up_email_proceed(message: Message, state: FSMContext) -> None:
    """Accepts email, updates state data, sets state that awaits password1."""
    await state.update_data(email=message.text)
    await state.set_state(Registration.password1)
    await message.answer(
        'Введите пароль. Используйте символ || в начале и конце пароля, если хотите скрыть содержимое.',
        reply_markup=cancel_inline_kb,
    )


@router.message(Registration.password1)
async def sign_up_password1_proceed(message: Message, state: FSMContext) -> None:
    """Accepts password1, updates state data, sets state that awaits password2."""
    await state.update_data(password1=message.text)
    await state.set_state(Registration.password2)
    await message.answer(
        'Введите пароль еще раз, чтобы его подтвердить.',
        reply_markup=cancel_inline_kb,
    )


@router.message(Registration.password2)
async def sign_up_password2_proceed(message: Message, state: FSMContext) -> None:
    """Accepts password2, makes sign up request to API, calls login if no email confirmation needed."""
    await state.update_data(password2=message.text)

    data = await state.get_data()

    async with aiohttp.ClientSession() as session:
        api_request_logging(SIGN_UP_URL, data=data, method='post')
        async with session.post(url=SIGN_UP_URL, data=data) as response:
            match response.status:
                case HTTPStatus.OK:
                    response_data = await response.json()
                    await message.answer(
                        response_data.get('detail'),
                        reply_markup=initial_kb,
                    )
                case HTTPStatus.NO_CONTENT:
                    await message.answer(
                        'Вы успешно зарегистрировались! Выполняется вход...'
                    )
                    # execute authentication after succeed sign up if no email confirmation
                    await login_password_proceed(message, state)
                case HTTPStatus.BAD_REQUEST:
                    await send_validation_errors(message, state, response)
                case _:
                    await send_error_message(message, state, response)
