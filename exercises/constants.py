"""Exercises constants."""

import types
from datetime import time

from core.constants import AmountLimits

exercises_lookups = types.SimpleNamespace()
exercises_lookups.TRANSLATOR_EXERCISE_SLUG = 'translator'
exercises_lookups.ASSOCIATE_EXERCISE_SLUG = 'associate'

MAX_TEXT_ANSWER_LENGTH = 1024


class ExercisesAmountLimits(AmountLimits):
    """Amount limits constants."""

    EXERCISE_MAX_WORDS = 100
    EXERCISE_MAX_WORD_SETS = 50
    TRANSLATOR_MAX_TIME_LIMIT = time(0, 5, 0)
    TRANSLATOR_MIN_TIME_LIMIT = time(0, 0, 30)
    EXERCISE_MAX_REPETITIONS_AMOUNT = 10
    EXERCISE_MIN_REPETITIONS_AMOUNT = 1


class ExercisesLengthLimits:
    """Length limits constants."""

    MAX_SET_NAME_LENGTH = 64
