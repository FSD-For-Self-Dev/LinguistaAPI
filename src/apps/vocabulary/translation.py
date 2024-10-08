"""Vocabulary app internationalization."""

from modeltranslation.translator import TranslationOptions, register

from .models import WordType


@register(WordType)
class TypeTranslationOptions(TranslationOptions):
    """
    Internationalization settings for fields of the WordType model.
    """

    fields = ('name',)
