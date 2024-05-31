import logging
from http import HTTPStatus

import requests
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.keyboards import initial_kb

logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

router = Router()


@router.message(CommandStart())
async def echo_hi(message: Message):
    await message.answer(
        f'Привет {message.from_user.first_name}! Я ЛингвистА-бот 🤖',
        reply_markup=initial_kb,
    )


@router.message(F.text == 'Просмотр языков интерфейса')
async def languages_interface_available(message: Message):
    url = 'http://localhost:8000/ru/api/languages/interface/'
    response = requests.get(url)
    logging.info(f'Статус-код для languages_interface_available {response.status_code}')
    if response.status_code == HTTPStatus.OK:
        data: dict = response.json()
        available_languages = data.get('results')
        logging.info(f"////////////'{available_languages}'///////////////")
        if len(available_languages) == 0:
            await message.answer('Пока информация отсутствует...')
        else:
            await message.answer('ok')
    else:
        await message.answer('Что-то пошло не так. Попробуйте позже.')


# @router.message(F.text == 'Доступные языки')
# async def show_all_languages(message: Message):
#     url = 'http://localhost:8000/ru/api/languages/all/'
#     response = requests.get(url)
#     logging.info(f"////////////'{response.status_code}'///////////////")
#     if response.status_code == HTTPStatus.OK:
#         data = response.json()
#         # logging.info(f"////////////'{data}'///////////////")
#         languages = data['results']
#         language_names = []
#         for i in range(len(languages)):
#             language_names.append(languages[i]['name'])
#         x = ','.join(language_names)
#         # language_name = languages[0]['name']
#         await message.answer(f'Доступные языки: <b>{x}</b>')
#     else:
#         await message.answer('Что-то пошло не так. Попробуйте позже.')


@router.message(F.text == 'Выведи список изучаемых мною языков')
async def get_my_languages(message: Message, state: FSMContext):
    data = await state.get_data()
    logging.info(f"////////////'{data}'///////////////")
    token = data.get('token')
    if not token:
        await message.answer('Токен не найден. Пожалуйста, пройдите аутентификацию.')
        return
    url = 'http://localhost:8000/ru/api/languages/'
    headers = {'Authorization': f'Token {token}'}
    response = requests.get(url, headers=headers)
    logging.info(f"////////////'{response.status_code}'///////////////")
    data = response.json()
    languages = data['results']
    language_names = []

    for language_data in languages:
        language_name = language_data['language']['name']
        language_names.append(language_name)

    languages_str = ', '.join(language_names)

    await message.answer(f'{languages_str}')


async def no_intiendo(message: Message):
    await message.answer(f'Не понимаю, что значит {message.text}')
