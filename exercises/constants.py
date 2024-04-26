"""Константы приложения exercises."""
from datetime import time

from core.constants import AmountLimits


class ExercisesAmountLimits(AmountLimits):
    EXERCISE_MAX_WORDS = 100
    EXERCISE_MAX_WORD_SETS = 50
    TRANSLATOR_MAX_TIME_LIMIT = time(0, 5, 0)
    TRANSLATOR_MIN_TIME_LIMIT = time(0, 0, 30)
    EXERCISE_MAX_REPETITIONS_AMOUNT = 10
    EXERCISE_MIN_REPETITIONS_AMOUNT = 1


class ExercisesLengthLimits:
    MAX_SET_NAME_LENGTH = 64
