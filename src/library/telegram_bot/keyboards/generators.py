"""Inline markups generators."""


from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from keyboards.core import (
    cancel_button,
    return_button,
    forward_button,
    backward_button,
    get_page_num_button,
    get_forward_button,
    get_backward_button,
)
from handlers.vocabulary.constants import (
    VOCABULARY_WORDS_MARKUP_SIZE,
    LEARNING_LANGUAGES_MARKUP_SIZE,
    COLLECTIONS_MARKUP_SIZE,
    ADDITIONALS_MARKUP_SIZE,
)


load_dotenv()


async def generate_vocabulary_markup(
    state: FSMContext,
    words_paginated: dict,
    control_buttons: list[InlineKeyboardButton] = [],
) -> InlineKeyboardMarkup | None:
    """Returns markup that contains paginated user words."""
    state_data = await state.get_data()
    language_name = state_data.get('language_choose')

    try:
        words_list: list = state_data.get('vocabulary_words_list')[language_name]
    except TypeError:
        words_list: list = state_data.get('vocabulary_words_list')

    pages_total_amount = state_data.get('pages_total_amount')
    page_num = state_data.get('page_num')

    page: list = words_paginated.get(page_num, [])
    if not page:
        return None

    keyboard_builder = InlineKeyboardBuilder()
    for word_info in page:
        word_slug = word_info['slug']
        word_text = word_info['text']
        word_index = words_list.index({'text': word_text, 'slug': word_slug})
        keyboard_builder.add(
            InlineKeyboardButton(
                text=word_text, callback_data=f'word_profile__{word_index}'
            )
        )

    keyboard_builder.adjust(VOCABULARY_WORDS_MARKUP_SIZE)

    if pages_total_amount and pages_total_amount > 1:
        page_num_button = get_page_num_button(
            page_num,
            pages_total_amount,
            callback_data=f'choose_page__vocabulary__{language_name}',
        )
        forward_button = get_forward_button(f'forward__vocabulary__{language_name}')
        backward_button = get_backward_button(f'backward__vocabulary__{language_name}')
        keyboard_builder.row(backward_button, page_num_button, forward_button)

    keyboard_builder.row(*control_buttons)
    keyboard_builder.row(return_button)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())


async def generate_word_customization_markup(
    additions_field: str, additions_data: dict
) -> InlineKeyboardMarkup:
    """Returns keyboard that contains word additions current data with update, delete options."""
    keyboard_builder = InlineKeyboardBuilder()

    match additions_field:
        case (
            'examples'
            | 'definitions'
            | 'synonyms'
            | 'antonyms'
            | 'forms'
            | 'similars'
            | 'types'
            | 'form_groups'
            | 'tags'
            | 'collections'
        ):
            keyboard_builder.add(
                *[
                    InlineKeyboardButton(
                        text=additional_value,
                        callback_data=f'customizing_edit_{additional_index}',
                    )
                    for additional_index, additional_value in enumerate(additions_data)
                ]
            )
            keyboard_builder.adjust(ADDITIONALS_MARKUP_SIZE)

        case 'translations':
            for additional_index, additional_value in enumerate(additions_data):
                language_name, translation_value = additional_value
                if language_name:
                    button_text = f'{translation_value} ({language_name})'
                else:
                    button_text = f'{translation_value}'
                keyboard_builder.add(
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f'customizing_edit_{additional_index}',
                    )
                )
            keyboard_builder.adjust(ADDITIONALS_MARKUP_SIZE)
            keyboard_builder.row(
                InlineKeyboardButton(
                    text='Сменить язык переводов',
                    callback_data='customizing_change_translations_language',
                )
            )

        case 'image_associations':
            keyboard_builder.row(
                InlineKeyboardButton(
                    text='Очистить все картинки',
                    callback_data='customizing_clear_image_associations',
                )
            )

        case 'note':
            pass

        case _:
            raise AssertionError('Word create: Unknown customization field was passed')

    keyboard_builder.row(return_button)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())


async def generate_word_profile_markup(response_data: dict) -> InlineKeyboardMarkup:
    """Returns markup that contains word profile info."""
    translations_count = response_data.get('translations_count')
    examples_count = response_data.get('examples_count')
    definitions_count = response_data.get('definitions_count')
    image_associations_count = response_data.get('image_associations_count')
    synonyms_count = response_data.get('synonyms_count')
    antonyms_count = response_data.get('antonyms_count')
    forms_count = response_data.get('forms_count')
    similars_count = response_data.get('similars_count')
    collections_count = response_data.get('collections_count')

    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.add(
        InlineKeyboardButton(
            text=f'Переводы {translations_count}',
            callback_data='additions_list__translations',
        ),
        InlineKeyboardButton(
            text=f'Примеры {examples_count}',
            callback_data='additions_list__examples',
        ),
        InlineKeyboardButton(
            text=f'Определения {definitions_count}',
            callback_data='additions_list__definitions',
        ),
        InlineKeyboardButton(
            text=f'Картинки-ассоциации {image_associations_count}',
            callback_data='additions_list__image_associations',
        ),
        InlineKeyboardButton(
            text=f'Синонимы {synonyms_count}',
            callback_data='additions_list__synonyms',
        ),
        InlineKeyboardButton(
            text=f'Антонимы {antonyms_count}',
            callback_data='additions_list__antonyms',
        ),
        InlineKeyboardButton(
            text=f'Формы {forms_count}', callback_data='additions_list__forms'
        ),
        InlineKeyboardButton(
            text=f'Похожие слова {similars_count}',
            callback_data='additions_list__similars',
        ),
        InlineKeyboardButton(
            text=f'Коллекции {collections_count}',
            callback_data='additions_list__collections',
        ),
    )

    keyboard_builder.adjust(3)

    favorite = response_data['favorite']
    if favorite:
        keyboard_builder.row(
            InlineKeyboardButton(
                text='Удалить из избранного', callback_data='word_favorite__delete'
            )
        )
    else:
        keyboard_builder.row(
            InlineKeyboardButton(
                text='Добавить в избранное', callback_data='word_favorite__post'
            )
        )

    is_problematic = response_data['is_problematic']
    if is_problematic:
        keyboard_builder.row(
            InlineKeyboardButton(
                text='Удалить из проблемных', callback_data='problematic_toggle__delete'
            )
        )
    else:
        keyboard_builder.row(
            InlineKeyboardButton(
                text='Отметить проблемным', callback_data='problematic_toggle__post'
            )
        )

    keyboard_builder.row(return_button)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())


async def generate_additions_list_markup(
    additions_field: str, additions_data: dict
) -> InlineKeyboardMarkup:
    """Returns markup that contains word additions list."""
    keyboard_builder = InlineKeyboardBuilder()

    match additions_field:
        case 'examples' | 'definitions' | 'types' | 'form_groups' | 'tags':
            keyboard_builder.add(
                *[
                    InlineKeyboardButton(
                        text=additional_value,
                        callback_data=f'additions_profile__{additional_index}',
                    )
                    for additional_index, additional_value in enumerate(additions_data)
                ]
            )
            keyboard_builder.adjust(ADDITIONALS_MARKUP_SIZE)

        case 'synonyms' | 'antonyms' | 'forms' | 'similars':
            keyboard_builder.add(
                *[
                    InlineKeyboardButton(
                        text=word,
                        callback_data=f'wp_word_profile__{word_index}',
                    )
                    for word_index, word in enumerate(additions_data)
                ]
            )
            keyboard_builder.adjust(VOCABULARY_WORDS_MARKUP_SIZE)

        case 'translations':
            for additional_index, additional_value in enumerate(additions_data):
                keyboard_builder.add(
                    InlineKeyboardButton(
                        text=additional_value[1],
                        callback_data=f'additions_profile__{additional_index}',
                    )
                )
            keyboard_builder.adjust(ADDITIONALS_MARKUP_SIZE)

        case 'collections':
            keyboard_builder.add(
                *[
                    InlineKeyboardButton(
                        text=collection_title,
                        callback_data=f'collection_profile__{collection_index}',
                    )
                    for collection_index, collection_title in enumerate(additions_data)
                ]
            )
            keyboard_builder.adjust(ADDITIONALS_MARKUP_SIZE)

        case 'image_associations':
            pass

        case _:
            raise AssertionError('Word create: Unknown customization field was passed')

    keyboard_builder.row(return_button)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())


async def generate_learning_languages_markup(
    state: FSMContext,
    callback_data: str = 'word_create_language',
    control_buttons: list = [],
) -> InlineKeyboardMarkup:
    """Returns inline keyboard with learning languages names from state data."""
    state_data = await state.get_data()
    learning_languages_info: dict = state_data.get('learning_languages_info')

    try:
        keyboard_builder = InlineKeyboardBuilder()
        keyboard_builder.add(
            *[
                InlineKeyboardButton(
                    text=language_name,
                    callback_data=f'{callback_data}__{language_name}',
                )
                for language_name in learning_languages_info.keys()
            ]
        )
        keyboard_builder.adjust(LEARNING_LANGUAGES_MARKUP_SIZE)
        keyboard_builder.row(*control_buttons)
        keyboard_builder.row(cancel_button)
        return InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())

    except AttributeError:
        return None


async def generate_words_multiple_create_markup(
    state: FSMContext, words: list, words_paginated: dict
) -> InlineKeyboardMarkup:
    """Returns markup that contains paginated words."""
    state_data = await state.get_data()
    pages_total_amount = state_data.get('pages_total_amount')
    page_num = state_data.get('page_num')
    words_page: list = words_paginated.get(page_num, [])

    keyboard_builder = InlineKeyboardBuilder()
    for _, word in enumerate(words_page):
        word_index = list(words).index(word)
        keyboard_builder.add(
            InlineKeyboardButton(
                text=word, callback_data=f'word_create_multiple_edit__{word_index}'
            )
        )

    keyboard_builder.adjust(2)

    if pages_total_amount and pages_total_amount > 1:
        page_num_button = get_page_num_button(page_num, pages_total_amount)
        keyboard_builder.row(backward_button, page_num_button, forward_button)

    keyboard_builder.row(
        InlineKeyboardButton(text='Сохранить в словарь', callback_data='multiple_save')
    )
    keyboard_builder.row(
        InlineKeyboardButton(
            text='Сохранить в коллекции', callback_data='choose_collections'
        )
    )
    keyboard_builder.row(cancel_button)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())


async def generate_collections_markup(
    state: FSMContext,
    collections_paginated: dict,
    callback_data: str = 'collection_profile',
    *args,
    **kwargs,
) -> InlineKeyboardMarkup | None:
    """Returns markup that contains paginated collections."""
    state_data = await state.get_data()
    pages_total_amount = state_data.get('pages_total_amount')
    page_num = state_data.get('page_num')

    page: list = collections_paginated.get(page_num, [])
    if not page:
        return None

    keyboard_builder = InlineKeyboardBuilder()
    for collection_info in page:
        collection_title = collection_info['title']
        collections_list: list = state_data.get('collections_list')
        collection_index = collections_list.index(collection_info)
        keyboard_builder.add(
            InlineKeyboardButton(
                text=collection_title,
                callback_data=f'{callback_data}__{collection_index}',
            )
        )

    keyboard_builder.adjust(COLLECTIONS_MARKUP_SIZE)

    if pages_total_amount and pages_total_amount > 1:
        page_num_button = get_page_num_button(page_num, pages_total_amount)
        keyboard_builder.row(backward_button, page_num_button, forward_button)

    return_button = kwargs.get('return_button')
    if return_button:
        keyboard_builder.row(return_button)
    else:
        keyboard_builder.row(
            InlineKeyboardButton(text='Вернуться назад', callback_data='return_to_main')
        )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_builder.export())
