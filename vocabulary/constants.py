"""Vocabulary constants."""

from django.utils.translation import gettext as _


class VocabularyAmountLimits:
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
    MAX_FORM_GROUPS_AMOUNT = 4

    class Details:
        TYPES_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во типов')
        TAGS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во тегов')
        TRANSLATIONS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во переводов')
        NOTES_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во заметок')
        EXAMPLES_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во примеров')
        DEFINITIONS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во определений')
        FORMS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во форм')
        IMAGES_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во картинок-ассоциаций')
        QUOTES_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во цитат-ассоциаций')
        SYNONYMS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во синонимов')
        ANTONYMS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во антонимов')
        SIMILARS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во похожих слов')
        FORM_GROUPS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во групп форм')


class VocabularyLengthLimits:
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
