"""Vocabulary app internationalization."""

from modeltranslation.translator import TranslationOptions, register

from .models import Type


@register(Type)
class TypeTranslationOptions(TranslationOptions):
    """
    Internationalization settings for fields of the Type model.
    """

    fields = ('name',)
