"""Exercises app constants."""

import types


exercises_lookups = types.SimpleNamespace()
exercises_lookups.TRANSLATOR_EXERCISE_SLUG = 'translator'
exercises_lookups.ASSOCIATE_EXERCISE_SLUG = 'associate'

MAX_TEXT_ANSWER_LENGTH = 1024


class ExercisesLengthLimits:
    """Length limits constants."""

    MAX_SET_NAME_LENGTH = 64
