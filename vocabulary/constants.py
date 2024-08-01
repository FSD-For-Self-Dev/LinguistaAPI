"""Vocabulary constants."""

from core.constants import AmountLimits


class VocabularyAmountLimits(AmountLimits):
    """Amount limits constants."""

    MAX_TYPES_AMOUNT = 3
    MAX_TAGS_AMOUNT = 10
    MAX_TRANSLATIONS_AMOUNT = 24
    MAX_NOTES_AMOUNT = 10
    MAX_EXAMPLES_AMOUNT = 10
    MAX_DEFINITIONS_AMOUNT = 10
    MAX_FORMS_AMOUNT = 10
    MAX_IMAGES_AMOUNT = 10
    MAX_QUOTES_AMOUNT = 10
    MAX_SYNONYMS_AMOUNT = 16
    MAX_ANTONYMS_AMOUNT = 16
    MAX_SIMILARS_AMOUNT = 16
    MAX_FORMS_GROUPS_AMOUNT = 4


class LengthLimits:
    """Length limits constants."""

    MAX_WORD_LENGTH = 256
    MIN_WORD_LENGTH = 1
    MAX_TRANSLATION_LENGTH = 256
    MIN_TRANSLATION_LENGTH = 1
    MAX_DEFINITION_LENGTH = 512
    MIN_DEFINITION_LENGTH = 2
    MAX_EXAMPLE_LENGTH = 512
    MIN_EXAMPLE_LENGTH = 2
    MAX_NOTE_LENGTH = 512
    MIN_NOTE_LENGTH = 1
    MAX_COLLECTION_NAME_LENGTH = 32
    MIN_COLLECTION_NAME_LENGTH = 1
    MAX_COLLECTION_DESCRIPTION_LENGTH = 128
    MAX_TAG_LENGTH = 32
    MIN_TAG_LENGTH = 1
    MAX_FORMSGROUP_NAME_LENGTH = 64
    MIN_FORMSGROUP_NAME_LENGTH = 1
    MAX_QUOTE_TEXT_LENGTH = 256
    MAX_QUOTE_AUTHOR_LENGTH = 64


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
