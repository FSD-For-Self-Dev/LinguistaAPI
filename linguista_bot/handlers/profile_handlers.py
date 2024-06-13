import logging
from http import HTTPStatus
import json
import aiohttp
import requests
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from .constants import AVAILABLE_LANGUAGES, MY_LANGUAGES, LANGUAGE_TO_REMOVE
from keyboards.keyboards import initial_kb, profile_kb
from states.languages_states import Language


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
    logging.info(
        f"///{get_available_languages.__name__}///'{response.status_code}'///////////////"
    )
    if response.status_code == HTTPStatus.OK:
        data = response.json()
        # logging.info(f"////////////'{data}'///////////////")
        languages = data['results']
        language_names = []
        for i in range(len(languages)):
            language_names.append(languages[i]['name'])
        x = ','.join(language_names)
        # language_name = languages[0]['name']
        await message.answer(
            f'Доступные языки: <b>{x}</b>'
        )
    else:
        await message.answer(
            f'{get_available_languages.__name__} Что-то пошло не так. Попробуйте позже.'
        )


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


@router.message(F.text == 'Добавить изучаемый язык')
async def learn_new_language(message: Message, state: FSMContext):
    await state.set_state(Language.language_to_learn)
    await message.answer(
        'Напишите язык, который бы хотели изучить или введите'
        '"Доступные для изучения языки", чтобы узнать,'
        'какие языки доступны для изучения'
    )


@router.message(Language.language_to_learn)
async def get_new_language(message: Message, state: FSMContext):
    await state.update_data(language_to_learn=message.text)

    data = await state.get_data()
    language_to_learn = data.get('language_to_learn')
    token = data.get('token')
    if not token:
        await state.clear()
        await message.answer(
            'Токен не найден. Пожалуйста, пройдите аутентификацию.',
            reply_markup=initial_kb,
        )
        return
    language_data = [{'language': language_to_learn, 'level': 'string'}]
    language_data_json = json.dumps(language_data)
    headers = {'Authorization': f'Token {token}', 'Content-Type': 'application/json'}

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=MY_LANGUAGES, headers=headers, data=language_data_json
        ) as response:
            if response.status == HTTPStatus.CREATED:
                await message.answer('Вы успешно добавили новый язык!')
                await state.clear()
            else:
                response_data = await response.json()
                await message.answer(
                    f'Что-то пошло не так: {response.status}, {response_data}'
                )


# @router.message(F.text == 'Удалить изучаемый язык')
# async def learn_new_language(message: Message, state: FSMContext):
#     await state.set_state(Language.language_to_remove)
#     await message.answer(
#         'Напишите язык, который хотели бы удалить или введите'
#         '"Посмотреть список моих языков", чтобы узнать,'
#         'какие языки вы изучаете'
#     )


# @router.message(Language.language_to_remove)
# async def delete_my_language(message: Message, state: FSMContext):
#     await state.update_data(language_to_remove=message.text)
    
#     data = await state.get_data()
#     language_to_remove = data.get('language_to_remove')
#     token = data.get('token')
#     logging.info(
#         f"///{delete_my_language.__name__}///'{language_to_remove}'///////"
#     )
#     logging.info(
#         f"///{delete_my_language.__name__}///'{token}'///////"
#     )
#     if not token:
#         await state.clear()
#         await message.answer(
#             'Токен не найден. Пожалуйста, пройдите аутентификацию.',
#             reply_markup=initial_kb,
#         )
#         return
#     headers = {'Authorization': f'Token {token}', 'Content-Type': 'application/json'}
#     url = LANGUAGE_TO_REMOVE + language_to_remove.lower() + '/'
#     print(url)
#     async with aiohttp.ClientSession() as session:
#         async with session.delete(
#             url=url, headers=headers,
#         ) as response:
#             if response.status == HTTPStatus.NO_CONTENT:
#                 await message.answer('Вы успешно удалили язык!')
#                 await state.clear()
#             else:
#                 response_data = await response.json()
#                 await message.answer(
#                     f'Что-то пошло не так: {response.status}, {response_data}'
#                 )