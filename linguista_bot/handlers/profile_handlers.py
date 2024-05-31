import logging
from http import HTTPStatus
import json
import aiohttp
import requests
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .constants import AVAILABLE_LANGUAGES, MY_LANGUAGES
from keyboards.keyboards import cancel_kb, initial_kb, profile_kb
from states.languages_states import NewLanguage


router = Router()


@router.message(F.text == 'Мой профиль')
async def my_profile(message: Message):
    await message.answer(
        'Выберите пункт меню',
        reply_markup=profile_kb,
    )


@router.message(F.text == 'Доступные для изучения языки')
async def get_available_languages(message: Message):
    url = AVAILABLE_LANGUAGES
    response = requests.get(url)
    logging.info(f"///{get_available_languages.__name__}///'{response.status_code}'///////////////")
    if response.status_code == HTTPStatus.OK:
        data = response.json()
        # logging.info(f"////////////'{data}'///////////////")
        languages = data['results']
        language_names = []
        for i in range(len(languages)):
            language_names.append(languages[i]['name'])
        x = ','.join(language_names)
        # language_name = languages[0]['name']
        await message.answer(f'{get_available_languages.__name__} Доступные языки: <b>{x}</b>')
    else:
        await message.answer(f'{get_available_languages.__name__} Что-то пошло не так. Попробуйте позже.')


@router.message(F.text == 'Посмотреть список моих языков')
async def get_my_languages(message: Message, state: FSMContext):
    data = await state.get_data()
    logging.info(f"////////////'{data}'///////////////")
    token = data.get('token')
    if not token:
        await message.answer(
            'Токен не найден. Пожалуйста, пройдите аутентификацию.',
            reply_markup=initial_kb,
        )
        return
    url = MY_LANGUAGES
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


@router.message(F.text == 'Учить новый язык')
async def learn_new_language(message: Message, state: FSMContext):
    await state.set_state(NewLanguage.new_language)
    await message.answer(
        'Напишите язык, который бы хотели изучить или введите'
        '"Доступные для изучения языки", чтобы узнать,'
        'какие языки доступны для изучения'
    )


@router.message(NewLanguage.new_language)
async def get_new_language(message: Message, state: FSMContext):
    await state.update_data(new_language=message.text)

    data = await state.get_data()
    language_to_learn = data.get('new_language')
    token = data.get('token')
    print(language_to_learn)
    print(token)
    if not token:
        await state.clear()
        await message.answer(
            'Токен не найден. Пожалуйста, пройдите аутентификацию.',
            reply_markup=initial_kb
        )
        return
    language_data = [{'language': language_to_learn, 'level': 'string'}]
    language_data_json = json.dumps(language_data)
    headers = {'Authorization': f'Token {token}', 'Content-Type': 'application/json'}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url=MY_LANGUAGES, headers=headers, data=language_data_json) as response:
            if response.status == HTTPStatus.CREATED:
                await message.answer('Вы успешно добавили новый язык!')
                # await state.clear()
            else:
                response_data = await response.json()
                await message.answer(f'Что-то пошло не так: {response.status}, {response_data}')