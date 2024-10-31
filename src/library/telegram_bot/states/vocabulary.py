"""Profile states."""

from aiogram.fsm.state import State

from .core import PreviousState


class Vocabulary(PreviousState):
    language_choose = State()
    list_retrieve = State()
    page_num = State()
    page_num_global = State()
    pages_total_amount = State()
    page_choose = State()
    photo_id = State()
    url = State()
    method = State()
    search = State()
    filtering = State()
    filter_field = State()
    counters_filter_value = State()
    date_filter_value = State()
    vocabulary_answer_text = State()
    vocabulary_send_request = State()
    vocabulary_paginated = State()
    vocabulary_words_list = State()
    vocabulary_words_count = State()


class WordProfile(PreviousState):
    retrieve = State()
    word_slug = State()
    word_text = State()
    images = State()
    response_data = State()


class WordCreate(PreviousState):
    create_start = State()
    language = State()
    text = State()
    text_edit = State()
    current_customizing_field = State()
    customizing_value = State()
    customizing_edit_index = State()
    customizing_edit_value = State()
    types = State()
    types_available = State()
    form_groups = State()
    tags = State()
    translations = State()
    translations_language = State()
    examples = State()
    definitions = State()
    image_associations = State()
    synonyms = State()
    antonyms = State()
    forms = State()
    similars = State()

    existing_word_id = State()
    new_word_text = State()
    existing_word_data = State()

    update = State()

    several_words = State()
    several_words_paginated = State()
    word_edit_index = State()
    language_multiple = State()
    add_to_collections = State()
    page_choose = State()
    collections_page_choose = State()

    word_create_handler = State()

    request_data = State()


class Collections(PreviousState):
    collections_send_request = State()
    collections_paginated = State()
    collections_count = State()
    collections_list = State()
    list_retrieve = State()
    retrieve = State()
    search = State()
    ordering = State()
    filtering = State()
    date_filter_value = State()
    language_filter_value = State()
    cb_collection_title = State()
    cb_collection_slug = State()
    new_words_language = State()
    new_words = State()


class CollectionUpdate(PreviousState):
    title = State()
    description = State()


class CollectionCreate(PreviousState):
    title = State()
    description = State()
    words_language = State()
    words = State()
