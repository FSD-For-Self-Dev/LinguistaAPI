"""Core handlers."""

import os
import logging
import html

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from emoji import emojize
from dotenv import load_dotenv

from keyboards.core import initial_kb, main_kb, cancel_inline_kb
from states.core import Core

from .utils import cancel, choose_page, get_next_page, get_previous_page


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    """Sends welcome message."""
    await message.answer(
        emojize(
            f'Привет, {message.from_user.first_name}! '
            f'Чтобы пользоваться ботом, необходимо войти в свой аккаунт Лингвисты! 👾'
        ),
        reply_markup=initial_kb,
    )


@router.message(F.text == 'Вернуться в меню')
@router.callback_query(F.data == 'return_to_main')
async def return_to_main(message: Message | CallbackQuery, state: FSMContext) -> None:
    """Sends main keyboard."""
    if isinstance(message, CallbackQuery):
        await message.answer('Вернуться назад')
        message = message.message
    await message.answer(text='Выберите пункт меню.', reply_markup=main_kb)


@router.message(F.text == 'Вернуться назад')
@router.message(F.text == 'Отмена')
@router.message(F.text == 'Отменить')
@router.callback_query(F.data == 'cancel')
@router.callback_query(F.data == 'return')
async def return_to_previous_state(
    message: Message | CallbackQuery, state: FSMContext
) -> None:
    """Runs previous state handler or returns to initial state."""
    state_data = await state.get_data()
    previous_state_handler = state_data.get('previous_state_handler')

    if isinstance(message, CallbackQuery):
        match message.data:
            case 'cancel':
                await message.answer('Отмена')
            case 'return':
                await message.answer('Вернуться назад')
            case _:
                await message.answer('Отмена')

        message = message.message

    if previous_state_handler:
        await state.update_data(create_start=False)
        await message.answer('Возвращаюсь...')
        await previous_state_handler(message, state)
    else:
        await cancel(message, state)


@router.callback_query(F.data == 'forward')
async def forward_choose_collections_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Updates state data with next page number, sends pagination handler answer."""
    state_data = await state.get_data()
    await get_next_page(state)
    await state_data.get('pagination_handler')(callback_query, state)
    await callback_query.message.delete()


@router.callback_query(F.data == 'backward')
async def backward_choose_collections_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Updates state data with previous page number, sends pagination handler answer."""
    state_data = await state.get_data()
    await get_previous_page(state)
    await state_data.get('pagination_handler')(callback_query, state)
    await callback_query.message.delete()


@router.callback_query(F.data == 'choose_page')
async def choose_page_several_words_callback(
    callback_query: CallbackQuery, state: FSMContext
) -> None:
    """Sets state that awaits page number."""
    state_data = await state.get_data()
    await state.set_state(Core.choose_page_num)
    await state.update_data(previous_state_handler=state_data.get('pagination_handler'))

    await callback_query.answer('Выбор страницы')

    await callback_query.message.answer(
        'Введите номер нужной страницы.',
        reply_markup=cancel_inline_kb,
    )


@router.message(Core.choose_page_num)
async def choose_page_proceed(message: Message, state: FSMContext) -> None:
    """Accepts page number, makes request for chosen page, sends pagination handler answer."""
    state_data = await state.get_data()
    await choose_page(message, state)
    await state_data.get('pagination_handler')(message, state)
    await message.delete()


@router.message(F.text)
async def unknown_command(message: Message) -> None:
    """Handler for unknown commands."""
    unknown_command = html.escape(message.text)
    await message.answer(f'Неизвестная команда: {unknown_command}')
