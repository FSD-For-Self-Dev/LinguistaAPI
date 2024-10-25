"""Some useful utils."""

import os
import logging

import aiohttp
from aiogram.types import (
    Message,
    BufferedInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.fsm.context import FSMContext
import aiohttp.client_reqrep
from dotenv import load_dotenv

from keyboards.core import initial_kb, return_kb, cancel_button
from keyboards.user_profile import profile_kb
from handlers.vocabulary.constants import fields_pretty, additionals_pretty


load_dotenv()

logging.basicConfig(
    level=getattr(logging, os.getenv('AIOGRAM_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def get_authentication_headers(
    token_auth=True, content_type='json', *args, **kwargs
) -> dict | None:
    """Returns dict of request headers."""
    if token_auth:
        token = kwargs.get('token', '')
        if token:
            match content_type:
                case 'json':
                    return {
                        'Authorization': f'Token {token}',
                        'Content-Type': 'application/json',
                    }
                case _:
                    return {'Authorization': f'Token {token}'}
    return None


async def cancel(message: Message, state: FSMContext) -> None:
    """Clears state and returns to initial state"""
    await state.clear()
    await message.answer(
        'Операция отменена. Зарегистрируйтесь или войдите для продолжения.',
        reply_markup=initial_kb,
    )


async def send_error_message(
    message: Message, state: FSMContext, response: aiohttp.client_reqrep.ClientResponse
) -> None:
    """Sends error message when some unexpected error occured."""
    await state.clear()
    response_data = await response.json()
    await message.answer(
        f'Кажется, что-то пошло не так. Код ответа: {response.status} 👾',
        reply_markup=return_kb,
    )
    logger.debug(
        f'During login API returned {response.status} status response: {response_data}'
    )


async def send_unauthorized_response(message: Message, state: FSMContext) -> None:
    """Sends unauthorized error message."""
    await state.clear()
    await message.answer(
        'Зарегистрируйтесь или войдите для продолжения.',
        reply_markup=initial_kb,
    )


async def send_validation_errors(
    message: Message, state: FSMContext, response: aiohttp.client_reqrep.ClientResponse
) -> None:
    """Sends validation errors messages."""
    response_data: dict = await response.json()
    answer_text = '🚫 Присутствуют ошибки в переданных значениях: \n\n'
    all_fields_pretty = fields_pretty | additionals_pretty

    for invalid_field, messages in response_data.items():
        answer_text += f'{all_fields_pretty[invalid_field][0]}: \n'
        for detail_message in messages:
            if isinstance(detail_message, str):
                answer_text += f'\t- {detail_message} \n'
            else:
                for key, value in detail_message.items():
                    value_str = '\n\t\t\t\t-- '.join(value)
                    key_str = all_fields_pretty[key][0]
                    answer_text += f'\t- {key_str}: \n\t\t\t\t-- {value_str} \n'
        answer_text += '\n'

    answer_text += 'Пожалуйста, исправьте ошибки и повторите попытку.'
    await message.answer(answer_text)


async def send_conflicts_errors(
    message: Message, state: FSMContext, response: aiohttp.client_reqrep.ClientResponse
) -> None:
    """Sends conflicts errors messages."""
    response_data: dict = await response.json()
    try:
        match response_data['exception_code']:
            case 'amount_limit_exceeded':
                detail_message = response_data.get('detail')
                amount_limit = response_data.get('amount_limit')
                detail_message += f' ({amount_limit})'
                await message.answer(detail_message)
            case 'already_exist':
                detail_message = response_data.get('detail')
                existing_word = response_data.get('existing_object')

                existing_word_note = (
                    existing_word['note']
                    if existing_word['note']
                    else '<i>Не указана</i>'
                )
                existing_word_types_str = (
                    ', '.join(existing_word['types'])
                    if existing_word['types']
                    else '<i>Не указаны</i>'
                )
                existing_word_form_groups_str = (
                    ', '.join(
                        [
                            form_group['name']
                            for form_group in existing_word['form_groups']
                        ]
                    )
                    if existing_word['form_groups']
                    else '<i>Не указаны</i>'
                )
                existing_word_tags_str = (
                    ', '.join([tag['name'] for tag in existing_word['tags']])
                    if existing_word['tags']
                    else '<i>Не указаны</i>'
                )
                existing_word_translations = existing_word['translations_count']
                existing_word_examples = existing_word['examples_count']
                existing_word_definitions = existing_word['definitions_count']
                existing_word_image_associations = existing_word['images_count']
                existing_word_synonyms = existing_word['synonyms_count']
                existing_word_antonyms = existing_word['antonyms_count']
                existing_word_forms = existing_word['forms_count']
                existing_word_similars = existing_word['similars_count']
                existing_word_collections = existing_word['collections_count']
                detail_message += (
                    f'\n\n<b>{existing_word["text"]}</b>\n\n'
                    f'Профиль слова из вашего словаря:\n\n'
                    f'Язык: {existing_word["language"]}\n'
                    f'Заметка: {existing_word_note}\n'
                    f'Группы форм (форма): {existing_word_types_str}\n'
                    f'Типы (части речи): {existing_word_form_groups_str}\n'
                    f'Теги: {existing_word_tags_str}\n\n'
                    f'Переводы: {existing_word_translations}\n'
                    f'Примеры: {existing_word_examples}\n'
                    f'Определения: {existing_word_definitions}\n'
                    f'Картинки-ассоциации: {existing_word_image_associations}\n'
                    f'Синонимы: {existing_word_synonyms}\n'
                    f'Антонимы: {existing_word_antonyms}\n'
                    f'Формы: {existing_word_forms}\n'
                    f'Похожие слова: {existing_word_similars}\n'
                    f'Коллекции: {existing_word_collections}\n'
                )

                await state.update_data(word_existing_id=existing_word['id'])
                await message.answer(
                    detail_message,
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text='Обновить',
                                    callback_data='word_create_update_existing',
                                ),
                            ],
                            [
                                cancel_button,
                            ],
                        ]
                    ),
                )
            case _:
                detail_message = response_data.get('detail')
                await message.answer(detail_message)

    except KeyError:
        detail_message = response_data.get('detail')
        await message.answer(detail_message)


async def send_user_profile_answer(
    session: aiohttp.ClientSession,
    message: Message,
    state: FSMContext,
    response_data: dict,
    *args,
    **kwargs,
) -> None:
    """Sends user profile info."""
    username = response_data['username']
    first_name = response_data['first_name'] or '<i>Не заполнено</i>'
    words_count = response_data['words_count']
    profile_image_url = response_data['image']

    native_languages = (
        ', '.join(response_data['native_languages'])
        if response_data['native_languages']
        else '<i>Не заполнено</i>'
    )

    learning_languages_count = response_data['learning_languages_count']
    learning_languages = (
        '\n'.join(
            [
                '\t\t- '
                + language['language']['name_local']
                + ' ('
                + str(language['words_count'])
                + ')'
                for language in response_data['learning_languages']
            ]
        )
        if response_data['learning_languages']
        else '<i>Не заполнено</i>'
    )

    answer_text = '\n'.join(
        (
            f'<b>Профиль пользователя {username}</b>',
            '',
            f'<b>Имя:</b> {first_name}',
            f'<b>Родные языки:</b> {native_languages}',
            f'<b>Мощность словаря (общее кол-во слов):</b> {words_count}',
            '',
            f'<b>Количество изучаемых языков:</b> {learning_languages_count}',
            '<b>Изучаемые языки:</b>',
            f'{learning_languages}',
        )
    )

    if profile_image_url:
        # get image file from url
        headers = kwargs.get('headers', {})
        async with session.get(
            url=profile_image_url, headers=headers
        ) as image_response:
            profile_image = await image_response.content.read()
            profile_image_filename = profile_image_url.split('/')[-1]
        # send image file with text
        await message.answer_photo(
            photo=BufferedInputFile(
                file=profile_image, filename=profile_image_filename
            ),
            caption=answer_text,
            reply_markup=profile_kb,
        )
    # send only text
    else:
        await message.answer(
            answer_text,
            reply_markup=profile_kb,
        )


def api_request_logging(url, data=None, headers=None, method='get') -> None:
    logger.debug(
        f'Sending request to API url: {url} (method: {method}, headers: {headers}, data: {data})'
    )
