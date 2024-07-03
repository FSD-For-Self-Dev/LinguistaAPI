"""Core serializer fields."""

from typing import Any

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field


@extend_schema_field({'type': 'string'})
class ReadableHiddenField(serializers.Field):
    """Поле для автозаполнения при записи, но доступное при чтении."""

    def __init__(
        self,
        slug_field: str = None,
        serializer_class: Any = None,
        many: bool = False,
        **kwargs,
    ) -> None:
        assert 'default' in kwargs, 'default is a required argument.'
        assert (
            slug_field is not None or serializer_class is not None
        ), 'slug_field or serializer_class argument is required.'
        self.slug_field = slug_field
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
        return getattr(obj, self.slug_field)

    def validate_empty_values(self, data: Any) -> tuple[bool, Any]:
        return (True, self.get_default())

    def get_default(self) -> Any:
        return self.default(self)


class ReadWriteSerializerMethodField(serializers.SerializerMethodField):
    """Поле для чтения и записи полей вне модели."""

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
    """Поле SerializerMethodField с возможностью передать аргументы в метод."""

    def __init__(self, method_name: str | None = None, **kwargs) -> None:
        super().__init__(method_name)
        self.func_kwargs = kwargs

    def to_representation(self, value: Any) -> Any:
        method = getattr(self.parent, self.method_name)
        return method(value, **self.func_kwargs)
