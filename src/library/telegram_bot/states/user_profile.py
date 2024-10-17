"""User profile states."""

from aiogram.fsm.state import State

from .core import PreviousState


user_profile_retrieve = State()


class UserProfileUpdate(PreviousState):
    options = State()
    profile_image = State()
    native_languages = State()
    first_name = State()


class AddLearningLanguage(PreviousState):
    language = State()
