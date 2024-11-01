"""User profile states."""

from aiogram.fsm.state import State, StatesGroup


class UserProfile(StatesGroup):
    retrieve = State()
    update_options = State()
    profile_image_update = State()
    native_languages_update = State()
    first_name_update = State()
    learning_languages_info = State()
    native_languages_info = State()


class AddLearningLanguage(StatesGroup):
    language = State()
