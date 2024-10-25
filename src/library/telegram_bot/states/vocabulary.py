"""Profile states."""

from aiogram.fsm.state import State

from .core import PreviousState


class Vocabulary(PreviousState):
    language_choose = State()
    words_count = State()
    retrieve = State()
    page_num = State()
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
    answer_text = State()


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

    word_existing_id = State()

    update = State()

    several_words = State()
