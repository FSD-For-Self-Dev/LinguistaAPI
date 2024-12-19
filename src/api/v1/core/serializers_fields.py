"""API serializers custom fields."""

from typing import Any

from django.utils.translation import gettext as _
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.db.models import Model

from rest_framework import serializers
from rest_framework.fields import Field
from drf_spectacular.utils import extend_schema_field
from drf_extra_fields.fields import HybridImageField

from apps.core.constants import ExceptionDetails


class CurrentObjectDefault:
    """
    The current retrieved object as the default value for the field.
    Lookup field default is `slug`.
    """

    requires_context = True

    def __init__(self, object_lookup_model: Model, object_lookup_field: str = 'slug'):
        self.object_lookup_model = object_lookup_model
        self.object_lookup_field = object_lookup_field

    def __call__(self, serializer_field: Field) -> QuerySet:
        try:
            return self.object_lookup_model.objects.get(
                **{
                    self.object_lookup_field: serializer_field.context[
                        'view'
                    ].kwargs.get(self.object_lookup_field)
                }
            )
        except KeyError:
            return self.object_lookup_model.objects.none()

    def __repr__(self) -> str:
        return '%s()' % self.__class__.__name__


@extend_schema_field({'type': 'string'})
class ReadableHiddenField(serializers.Field):
    """
    Custom readable field with autofill through `default` argument.
    `representation_field` or `serializer_class` must be passed if `default`
    returns some Model instance.
    `representation_field` - instance field that will be represented.
    `serializer_class` - serializer through which instance will be represented.
    """

    def __init__(
        self,
        representation_field: str = None,
        serializer_class: Any = None,
        many: bool = False,
        **kwargs,
    ) -> None:
        assert 'default' in kwargs, 'default is a required argument.'
        self.representation_field = representation_field
        self.serializer_class = serializer_class
        self.many = many
        super().__init__(**kwargs)

    def get_value(self, dictionary: dict) -> serializers.empty:
        return serializers.empty

    def to_internal_value(self, data: Any) -> Any:
        return data

    def to_representation(self, obj: Any) -> Any:
        if self.serializer_class:
            return self.serializer_class(obj, many=self.many, context=self.context).data
        if self.representation_field:
            return getattr(obj, self.representation_field)
        return obj

    def validate_empty_values(self, data: Any) -> tuple[bool, Any]:
        return (True, self.get_default())

    def get_default(self) -> Any:
        return self.default(self)


class ReadWriteSerializerMethodField(serializers.SerializerMethodField):
    """
    Custom writable SerializerMethodField to be passed to serializer
    validated_data.
    """

    def __init__(self, method_name: str | None = None, **kwargs) -> None:
        self.method_name = method_name
        kwargs['source'] = '*'
        super(serializers.SerializerMethodField, self).__init__(**kwargs)

    def to_internal_value(self, data: Any) -> Any:
        return {self.field_name: data}

    def to_representation(self, value: Any) -> Any:
        method = getattr(self.parent, self.method_name)
        return method(value)


class KwargsMethodField(serializers.SerializerMethodField):
    """Custom SerializerMethodField with passing kwargs."""

    def __init__(self, method_name: str | None = None, **kwargs) -> None:
        super().__init__(method_name)
        self.func_kwargs = kwargs

    def to_representation(self, value: Any) -> Any:
        method = getattr(self.parent, self.method_name)
        return method(value, **self.func_kwargs)


class CapitalizedCharField(serializers.CharField):
    """Custom CharField to represent with capital letter."""

    def to_representation(self, value: str) -> str:
        return value.capitalize()


class CustomHybridImageField(HybridImageField):
    """
    Custom field to add invalid file validation error message to HybridImageField.
    """

    @property
    def INVALID_FILE_MESSAGE(self):
        raise serializers.ValidationError(ExceptionDetails.Images.INVALID_IMAGE_FILE)


class LanguageSlugRelatedField(serializers.SlugRelatedField):
    """Custom SlugRelatedField to change does_not_exist error message for languages."""

    default_error_messages = {
        'does_not_exist': _('Language {value} was not found. Check its spelling.'),
        'invalid': _('Invalid value.'),
    }


class TypeSlugRelatedField(serializers.SlugRelatedField):
    """Custom SlugRelatedField to change does_not_exist error message for word types."""

    default_error_messages = {
        'does_not_exist': _('Type {value} was not found. Check its spelling.'),
        'invalid': _('Invalid value.'),
    }


class CreatableSlugRelatedField(serializers.SlugRelatedField):
    """..."""

    def __init__(self, *args, **kwargs):
        self.author_current_user = kwargs.pop('author_current_user', None)
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        queryset = self.get_queryset()
        try:
            return queryset.get(**{self.slug_field: data.lower()})
        except ObjectDoesNotExist:
            if self.author_current_user:
                return queryset.create(
                    **{
                        self.slug_field: data,
                        'author': self.context.get('request').user,
                    }
                )
            return queryset.create(**{self.slug_field: data.lower()})
        except (TypeError, ValueError):
            self.fail('invalid')
