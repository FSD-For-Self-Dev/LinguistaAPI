from modeltranslation.translator import TranslationOptions, register

from vocabulary.models import Type


@register(Type)
class TypeTranslationOptions(TranslationOptions):
    """
    Класс настроек интернационализации полей модели Type.
    """

    fields = ('name',)
