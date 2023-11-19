from modeltranslation.translator import register, TranslationOptions
from .models import Type


@register(Type)
class TypeTranslationOptions(TranslationOptions):
    fields = ('name',)
