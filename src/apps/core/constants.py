"""Core constants."""

import os

from django.utils.translation import gettext_lazy as _

ADMIN_USERNAME = os.getenv('DJANGO_SUPERUSER_USERNAME', default='admin')

GENDERS = (
    ('M', _('Male')),
    ('F', _('Female')),
)

REGEX_TEXT_MASK = r"^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'()ёЁ ]*)$"
REGEX_TEXT_MASK_DETAIL = (
    'Acceptable characters: Latin letters (A-Z, a-z), '
    'Cyrillic letters (А-Я, а-я), Hyphen, '
    'Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. '
    'Make sure word begin with a letter.'
)

REGEX_HEXCOLOR_MASK = r'^#[\w]+$'
REGEX_HEXCOLOR_MASK_DETAIL = 'Color must be in hex format.'

MAX_IMAGE_SIZE_MB = 4  # 4 MB is max size for uploaded images
MAX_IMAGE_SIZE = MAX_IMAGE_SIZE_MB * 1024 * 1024  # uploaded images max size in bytes
