"""Exercises constants."""

import types
from datetime import time

from django.utils.translation import gettext as _

exercises_lookups = types.SimpleNamespace()
exercises_lookups.TRANSLATOR_EXERCISE_SLUG = 'translator'
exercises_lookups.ASSOCIATE_EXERCISE_SLUG = 'associate'

MAX_TEXT_ANSWER_LENGTH = 1024


class ExercisesAmountLimits:
    """Amount limits constants."""

    EXERCISE_MAX_WORDS_AMOUNT_LIMIT = 100
    MAX_WORD_SETS_AMOUNT_LIMIT = 50
    MAX_ANSWER_TIME_LIMIT = time(0, 5, 0)
    MIN_ANSWER_TIME_LIMIT = time(0, 0, 30)
    MAX_REPETITIONS_AMOUNT_LIMIT = 10
    MIN_REPETITIONS_AMOUNT_LIMIT = 1

    class Details:
        WORDS_AMOUNT_EXCEEDED = _(
            'Превышено максимальное количество слов для тренировки'
        )
        WORD_SETS_AMOUNT_EXCEEDED = _('Превышено максимальное количество наборов слов')
        MAX_ANSWER_TIME_EXCEEDED = _(
            'Превышено максимальное ограничение времени ответа'
        )
        MIN_ANSWER_TIME_EXCEEDED = _('Превышено минимальное ограничение времени ответа')
        MAX_REPETITIONS_LIMIT_EXCEEDED = _(
            'Превышено максимальное ограничение количества повторов'
        )
        MIN_REPETITIONS_LIMIT_EXCEEDED = _(
            'Превышено минимальное ограничение количества повторов'
        )


class ExercisesLengthLimits:
    """Length limits constants."""

    MAX_SET_NAME_LENGTH = 64
