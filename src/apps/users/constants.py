"""Users app constants."""

from django.utils.translation import gettext_lazy as _

GENDERS = (
    ('M', _('Male')),
    ('F', _('Female')),
)

REGEX_NAME_MASK = r"^(\p{L}+)([\p{L}'`’ ]*)$"
REGEX_NAME_MASK_DETAIL = _(
    'Acceptable characters: Letters from any language, '
    'Apostrophe, Space. '
    'Make sure name begin with a letter.'
)


class UsersLengthLimits:
    """Length limits constants."""

    FIRST_NAME_MAX_LENGTH = 32
