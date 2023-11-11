"""Константы приложения vocabulary."""

MAX_TYPES_AMOUNT = 3
MAX_TAGS_AMOUNT = 10
MAX_TRANSLATIONS_AMOUNT = 16
MAX_NOTES_AMOUNT = 10
MAX_EXAMPLES_AMOUNT = 10
MAX_DEFINITIONS_AMOUNT = 10
MAX_FORMS_AMOUNT = 10
MAX_SYNONYMS_AMOUNT = 16
MAX_ANTONYMS_AMOUNT = 16
MAX_SIMILARS_AMOUNT = 16

REGEX_TEXT_MASK = (
    r'^[A-Za-zА-Яа-я]+[\-\!\?\.\,\:\'\ ]*$'
)
REGEX_MESSAGE = (
    'Acceptable characters: Latin letters (A-Z, a-z), '
    'Cyrillic letters (А-Я, а-я), Hyphen, '
    'Exclamation point, Question mark, Dot, Comma, Colon.'
    'Make sure word begin with a letter.'
)
