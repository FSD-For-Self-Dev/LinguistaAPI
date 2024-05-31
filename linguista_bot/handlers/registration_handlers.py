import logging
from http import HTTPStatus
import aiohttp
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from keyboards.keyboards import cancel_kb, initial_kb
from states.auth_states import RegistrationForm

from .constants import REGISTRATION_ENDPOINT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

router = Router()


@router.message(F.text == 'Отмена')
async def cancel_operation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        'Операция отменена. Зарегистрируйтесь или войдите для продолжения.',
        reply_markup=initial_kb,
    )


# @router.message(Command('register'))
@router.message(F.text == 'Я хочу зарегистрироваться')
async def register_me(message: Message, state: FSMContext):
    await state.set_state(RegistrationForm.username)
    await message.answer(
        'Введите логин/юзернейм для своего аккаунта или нажмите "Отмена".',
        reply_markup=cancel_kb,
    )


@router.message(RegistrationForm.username)
async def registration_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(RegistrationForm.password1)
    await message.answer(
        'Введите пароль или нажмите "Отмена" для отмены операции.',
        reply_markup=cancel_kb,
    )


@router.message(RegistrationForm.password1)
async def registration_password1(message: Message, state: FSMContext):
    await state.update_data(password1=message.text)
    await state.set_state(RegistrationForm.password2)
    await message.answer(
        'Повторите пароль или нажмите "Отмена" для отмены операции.',
        reply_markup=cancel_kb,
    )


@router.message(RegistrationForm.password2)
async def registration_password2(message: Message, state: FSMContext):
    await state.update_data(password2=message.text)

    data = await state.get_data()
    # data_json = json.dumps(data)
    async with aiohttp.ClientSession() as session:
        async with session.post(url=REGISTRATION_ENDPOINT, data=data) as response:
            if response.status == HTTPStatus.NO_CONTENT:
                await message.answer('Вы успешно зарегистрировались!')
                await state.clear()
            else:
                await message.answer(
                    f'Ошибка при запросе на сервер. Код: {response.status}'
                )
                response_json = await response.json()
                logging.error(f"////////////'{response_json}'///////////////")
                await state.clear()
