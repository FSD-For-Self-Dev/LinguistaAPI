"""Константы приложения users."""

from core.constants import AmountLimits


class UsersAmountLimits(AmountLimits):
    MAX_NATIVE_LANGUAGES_AMOUNT = 2
    MAX_LEARNING_LANGUAGES_AMOUNT = 5
