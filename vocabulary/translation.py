from modeltranslation.translator import TranslationOptions, register

from .models import Type


@register(Type)
class TypeTranslationOptions(TranslationOptions):
    fields = ('name',)
