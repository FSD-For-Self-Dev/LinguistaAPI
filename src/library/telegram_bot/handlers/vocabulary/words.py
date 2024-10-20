"""Words CRUD handlres."""

import os
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
)
from dotenv import load_dotenv

from states.vocabulary import WordCreate


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

router = Router()


# old staff


@router.message(F.text == 'Добавить новое слово')
async def add_new_word_in_vocabulary(message: Message, state: FSMContext):
    await state.set_state(WordCreate.language)
    # TODO сделать клавиатуру, которая отображала бы языки пользователя
    await message.answer('Выберите язык, который, слово из которого вы добавляете')


@router.message(WordCreate.language)
async def get_language_to_add_new_word(message: Message, state: FSMContext):
    await state.update_data(language=message.text)
    await state.set_state(WordCreate.text)
    await message.answer(
        'Теперь напечатайте слово, которое хотели бы добавить в словарь'
    )


@router.message(WordCreate.text)
async def get_new_word_in_vocabulary(message: Message, state: FSMContext):
    await state.update_data(new_word=message.text)
    data = await state.get_data()
    token = data.get('token')
    language = data.get('language')
    new_word = data.get('text')
    logging.info(
        f'{get_new_word_in_vocabulary.__name__}, language={language}, new_word={new_word}, token={token}'
    )
