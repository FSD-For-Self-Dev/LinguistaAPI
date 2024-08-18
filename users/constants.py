"""Users app constants."""

from django.utils.translation import gettext as _


class UsersAmountLimits:
    """Amount limits constants."""

    MAX_NATIVE_LANGUAGES_AMOUNT = 2
    MAX_LEARNING_LANGUAGES_AMOUNT = 5

    class Details:
        LEARNING_LANGUAGES_AMOUNT_EXCEEDED = _(
            'Превышено максимальное кол-во изучаемых языков'
        )
        NATIVE_LANGUAGES_AMOUNT_EXCEEDED = _(
            'Превышено максимальное кол-во родных языков'
        )
