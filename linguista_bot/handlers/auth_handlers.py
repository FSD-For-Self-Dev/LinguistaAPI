import logging
import requests
from aiogram.types import Message
from http import HTTPStatus
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from states import AuthForm
from linguista_bot.constants import AUTHORIZATION_ENDPOINT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

router = Router()


# @router.message(Command('auth'))
@router.message(F.text == 'Войти в аккаунт')
async def authorize_me(message: Message, state: FSMContext):
    # await state.clear()
    await state.set_state(AuthForm.username)
    await message.answer('Введите логин/юзернейм')


@router.message(AuthForm.username)
async def auth_form_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(AuthForm.password)
    await message.answer('Теперь введите пароль')


@router.message(AuthForm.password)
async def auth_form_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)

    data = await state.get_data()
    logging.info(f"////////////'{data}'///////////////")
    response = requests.post(AUTHORIZATION_ENDPOINT, data=data)
    if response.status_code == HTTPStatus.OK:
        response_data = response.json()
        logging.info(f"////////////'{response_data}'///////////////")
        token = response_data.get('key')
        logging.info(f"////////////'{token}'///////////////")
        if token:
            data = await state.update_data(token=token)
            print(data)
            data = await state.get_data()
            print(data)
            await message.answer('Вы успешно авторизовались!')
        else:
            await message.answer('Не удалось получить токен из ответа сервера.')
    else:
        await message.answer(
            f'Ошибка при запросе на сервер. Код: {response.status_code}'
        )
