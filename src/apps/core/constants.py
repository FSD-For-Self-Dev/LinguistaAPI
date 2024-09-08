"""Core constants."""

import os

from django.utils.translation import gettext_lazy as _

ADMIN_USERNAME = os.getenv('DJANGO_SUPERUSER_USERNAME', default='admin')

REGEX_TEXT_MASK = r"^(\p{L}+)([\p{L}-!?.,:/&'`’() ]*)$"
REGEX_TEXT_MASK_DETAIL = _(
    'Acceptable characters: Letters from any language, '
    'Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. '
    'Make sure word begin with a letter.'
)

REGEX_HEXCOLOR_MASK = r'^#[\w]+$'
REGEX_HEXCOLOR_MASK_DETAIL = 'Color must be in hex format.'

MAX_IMAGE_SIZE_MB = 4  # 4 MB is max size for uploaded images
MAX_IMAGE_SIZE = MAX_IMAGE_SIZE_MB * 1024 * 1024  # uploaded images max size in bytes

MAX_SLUG_LENGTH = 1024
