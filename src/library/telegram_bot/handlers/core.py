"""Core handlers."""

import os
import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from emoji import emojize
from dotenv import load_dotenv

from keyboards.core import initial_kb, main_kb

from .utils import cancel


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    """Send welcome message."""
    await message.answer(
        emojize(
            f'Привет {message.from_user.first_name}! '
            f'Чтобы пользоваться ботом, необходимо войти в свой аккаунт Лингвисты! 👾'
        ),
        reply_markup=initial_kb,
    )


@router.message(F.text == 'Вернуться в меню')
async def return_to_main(message: Message, state: FSMContext) -> None:
    """Send main keyboard."""
    await message.answer(text='Выберите пункт меню.', reply_markup=main_kb)


@router.message(F.text == 'Вернуться назад')
@router.message(F.text == 'Отмена')
@router.callback_query(F.data == 'cancel')
async def return_to_previous_state(
    message: Message | CallbackQuery, state: FSMContext
) -> None:
    """Run previous state handler or return to initial state."""
    state_data = await state.get_data()
    previous_state_handler = state_data.get('previous_state_handler')

    if type(message) is CallbackQuery:
        await message.answer('Отмена')
        message = message.message

    if previous_state_handler:
        await message.answer('Возвращаюсь...')
        await previous_state_handler(message, state)
    else:
        await cancel(message, state)


@router.message(F.text)
async def unknown_message(message: Message) -> None:
    await message.answer(f'Неизвестная команда: {message.text}')
