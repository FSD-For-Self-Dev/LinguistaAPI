from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .models import Language, Word


@extend_schema_field({'type': 'string'})
class ReadableHiddenField(serializers.Field):
    def __init__(self, slug_field=None, serializer_class=None, many=False, **kwargs):
        assert 'default' in kwargs, 'default is a required argument.'
        assert (
            slug_field is not None or serializer_class is not None
        ), 'slug_field or serializer_class argument is required.'
        self.slug_field = slug_field
        self.serializer_class = serializer_class
        self.many = many
        super().__init__(**kwargs)

    def get_value(self, dictionary):
        return serializers.empty

    def to_internal_value(self, data):
        return data

    def to_representation(self, obj):
        if self.serializer_class:
            return self.serializer_class(obj, many=self.many).data
        return getattr(obj, self.slug_field)

    def validate_empty_values(self, data):
        return (True, self.get_default())

    def get_default(self):
        return self.default(self)


class WordSameLanguageDefault:
    requires_context = True

    def __call__(self, serializer_field):
        request_data = serializer_field.context['request'].data
        try:
            return Language.objects.get(name=request_data['language'])
        except KeyError:
            return None

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class CurrentWordDefault:
    requires_context = True

    def __call__(self, serializer_field):
        request_word_slug = serializer_field.context['view'].kwargs.get('slug')
        try:
            return Word.objects.get(slug=request_word_slug)
        except KeyError:
            return None

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class ReadWriteSerializerMethodField(serializers.SerializerMethodField):
    """Поле для чтения и записи полей вне модели."""

    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs['source'] = '*'
        super(serializers.SerializerMethodField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        return {self.field_name: data}

    def to_representation(self, value):
        method = getattr(self.parent, self.method_name)
        return method(value)


class KwargsMethodField(serializers.SerializerMethodField):
    """Поле SerializerMethodField с возможностью передать аргументы в метод."""

    def __init__(self, method_name=None, **kwargs):
        super().__init__(method_name)
        self.func_kwargs = kwargs

    def to_representation(self, value):
        method = getattr(self.parent, self.method_name)
        return method(value, **self.func_kwargs)
