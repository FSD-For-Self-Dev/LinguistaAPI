import logging
from http import HTTPStatus

import requests
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.keyboards import cancel_kb, initial_kb, main_kb
from states.auth_states import AuthForm

from .constants import AUTHORIZATION_ENDPOINT

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
        reply_markup=initial_kb
    )


# @router.message(Command('auth'))
@router.message(F.text == 'Войти в аккаунт')
async def authorize_me(message: Message, state: FSMContext):
    # await state.clear()
    await state.set_state(AuthForm.username)
    await message.answer(
        'Введите логин/юзернейм или нажмите "Отмена" для отмены операции.',
        reply_markup=cancel_kb
    )


@router.message(AuthForm.username)
async def auth_form_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(AuthForm.password)
    await message.answer(
        'Теперь введите пароль или нажмите "Отмена" для отмены операции.',
        reply_markup=cancel_kb
    )


@router.message(AuthForm.password)
async def auth_form_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)

    data = await state.get_data()
    logging.info(f"{auth_form_password.__name__} '{data}'")
    response = requests.post(AUTHORIZATION_ENDPOINT, data=data)
    if response.status_code == HTTPStatus.OK:
        response_data = response.json()
        logging.info(f"{auth_form_password.__name__} '{response_data}'")
        token = response_data.get('key')
        logging.info(f"{auth_form_password.__name__} '{token}'")
        if token:
            data = await state.update_data(token=token)
            # print(data)
            data = await state.get_data()
            # print(data)
            await message.answer(
                'Вы успешно авторизовались!',
                reply_markup=main_kb,
            )
            return
        else:
            await message.answer(
                f'{auth_form_password.__name__} Не удалось получить токен из ответа сервера.'
            )
    else:
        await message.answer(
            f'{auth_form_password.__name__} Ошибка при запросе на сервер. Код: {response.status_code}'
        )
