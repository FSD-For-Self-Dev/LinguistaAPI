import logging
import requests
from aiogram.types import Message
from http import HTTPStatus
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from states import RegistrationForm
from linguista_bot.constants import REGISTRATION_ENDPOINT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

router = Router()


# @router.message(Command('register'))
@router.message(F.text == 'Я хочу зарегистрироваться')
async def register_me(message: Message, state: FSMContext):
    await state.set_state(RegistrationForm.username)
    await message.answer('Выберите логин/юзернейм')


@router.message(RegistrationForm.username)
async def registration_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(RegistrationForm.password1)
    await message.answer('Введите пароль')


@router.message(RegistrationForm.password1)
async def registration_password1(message: Message, state: FSMContext):
    await state.update_data(password1=message.text)
    await state.set_state(RegistrationForm.password2)
    await message.answer('Повторите пароль')


@router.message(RegistrationForm.password2)
async def registration_password2(message: Message, state: FSMContext):
    await state.update_data(password2=message.text)

    data = await state.get_data()
    response = requests.post(REGISTRATION_ENDPOINT, data=data)
    logging.info(f"////////////'{response.status_code}'///////////////")
    if response.status_code == HTTPStatus.NO_CONTENT:
        await message.answer('Вы успешно зарегистрировались!')
        await state.clear()
    else:
        await message.answer(
            f'Ошибка при запросе на сервер. Код: {response.status_code}'
        )
        response_json = response.json()
        logging.error(f"////////////'{response_json}'///////////////")
        await state.clear()
