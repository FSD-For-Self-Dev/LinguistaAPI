"""Константы приложения vocabulary."""


class AmountLimits:
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

    @staticmethod
    def get_error_message(limit_amount, limit_name):
        return (
            f'Лимит достигнут: нельзя добавить больше чем {limit_amount} {limit_name}.'
        )


class LengthLimits:
    MAX_WORD_LENGTH = 512
    MIN_WORD_LENGTH = 1
    MAX_TRANSLATION_LENGTH = 512
    MIN_TRANSLATION_LENGTH = 1
    MAX_DEFINITION_LENGTH = 1024
    MIN_DEFINITION_LENGTH = 2
    MAX_EXAMPLE_LENGTH = 1024
    MIN_EXAMPLE_LENGTH = 2
    MAX_NOTE_LENGTH = 4096
    MIN_NOTE_LENGTH = 1
    MAX_COLLECTION_NAME_LENGTH = 32
    MIN_COLLECTION_NAME_LENGTH = 1
    MAX_COLLECTION_DESCRIPTION_LENGTH = 512
    MAX_TAG_LENGTH = 32
    MIN_TAG_LENGTH = 1
    MAX_FORMSGROUP_NAME_LENGTH = 64
    MIN_FORMSGROUP_NAME_LENGTH = 1
    MAX_IMAGE_NAME_LENGTH = 64


REGEX_TEXT_MASK = r"^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'()ёЁ ]*)$"
REGEX_MESSAGE = (
    'Acceptable characters: Latin letters (A-Z, a-z), '
    'Cyrillic letters (А-Я, а-я), Hyphen, '
    'Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. '
    'Make sure word begin with a letter.'
)
