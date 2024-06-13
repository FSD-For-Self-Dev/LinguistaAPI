import logging
from http import HTTPStatus
import aiohttp
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from keyboards.keyboards import cancel_kb, initial_kb
from states.vocabulary_states import Word

from .constants import VOCABULARY_ENDPOINT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

router = Router()


@router.message(F.text == 'Добавить новое слово')
async def add_new_word_in_vocabulary(message: Message, state: FSMContext):
    await state.set_state(Word.language)
    # TODO сделать клавиатуру, которая отображала бы языки пользователя
    await message.answer('Выберите язык, который, слово из которого вы добавляете')


@router.message(Word.language)
async def get_language_to_add_new_word(message: Message, state: FSMContext):
    await state.update_data(language=message.text)
    await state.set_state(Word.new_word)
    await message.answer('Теперь напечатайте слово, которое хотели бы добавить в словарь')


@router.message(Word.new_word)
async def get_new_word_in_vocabulary(message: Message, state: FSMContext):
    await state.update_data(new_word=message.text)
    data = await state.get_data()
    token = data.get('token')
    language = data.get('language')
    new_word = data.get('new_word')
    logging.info(f'{get_new_word_in_vocabulary.__name__}, language={language}, new_word={new_word}, token={token}')
    