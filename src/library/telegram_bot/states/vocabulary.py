"""Profile states."""

from aiogram.fsm.state import State, StatesGroup

from .core import PreviousState


class Vocabulary(StatesGroup):
    language_choose = State()
    retrieve = State()
    page_num = State()
    pages_total_amount = State()
    page_choose = State()
    photo_id = State()
    url = State()
    search = State()
    filtering = State()
    filter_field = State()
    counters_filter_value = State()
    date_filter_value = State()
    answer_text = State()
    previous_state_handler = State()


class WordCreate(PreviousState):
    language = State()
    text = State()
    translations = State()
    image_associations = State()
    several_words = State()
    previous_state_handler = State()
