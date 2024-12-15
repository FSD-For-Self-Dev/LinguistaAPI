"""Languages app internationalization."""

from modeltranslation.translator import TranslationOptions, register

from .models import Language


@register(Language)
class LanguageTranslationOptions(TranslationOptions):
    """
    Internationalization settings for fields of the Language model.
    """

    fields = ('name', 'country')
