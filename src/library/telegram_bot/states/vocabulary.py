"""Profile states."""

from aiogram.fsm.state import State, StatesGroup


class Vocabulary(StatesGroup):
    language_choose = State()
    list_retrieve = State()
    page_choose = State()
    search = State()
    filtering = State()
    counters_filter_value = State()
    date_filter_value = State()


class WordProfile(StatesGroup):
    retrieve = State()


class WordCreate(StatesGroup):
    language = State()
    text = State()
    text_edit = State()
    customizing_value = State()
    customizing_edit_value = State()
    several_words = State()
    language_multiple = State()
    add_to_collections = State()


class Collections(StatesGroup):
    list_retrieve = State()
    retrieve = State()
    search = State()
    ordering = State()
    filtering = State()
    date_filter_value = State()
    language_filter_value = State()
    new_words_language = State()
    new_words = State()


class CollectionUpdate(StatesGroup):
    title = State()
    description = State()


class CollectionCreate(StatesGroup):
    title = State()
    description = State()
    words_language = State()
    words = State()
