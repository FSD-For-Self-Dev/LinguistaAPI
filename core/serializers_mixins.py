"""Core serializer mixins."""

import logging
from typing import Any, Type
from collections import OrderedDict

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Model
from django.db.models.query import QuerySet

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .serializers_fields import ReadWriteSerializerMethodField
from .exceptions import ObjectAlreadyExist, AmountLimitExceeded
from .utils import get_object_by_pk

logger = logging.getLogger(__name__)


class AlreadyExistSerializerHandler:
    """
    Custom mixin to use in ModelSerializer.
    Adds `ObjectAlreadyExist` custom exception handling.
    """

    already_exist_detail = ObjectAlreadyExist.default_detail

    def check_existing_obj(
        self, data: dict | OrderedDict, *args, **kwargs
    ) -> Type[Model] | None:
        """
        Check if object with passed data exists.
        Returns existing object if data the same, else raise the exception.
        """
        meta_model = self.Meta.model
        logger.debug(f'Model used: {meta_model}')

        # To get object that matches passed data for unique fields
        # (avoid IntegrityError), `get_object` method must be implemented in Model
        # or it will be gotten by objects filter with passed data
        # (an TypeError may be occured).
        if hasattr(meta_model, 'get_object'):
            logger.debug('Method used: get_object')

            _existing_obj = meta_model.get_object(data)
            logger.debug(f'Obtained existing object: {_existing_obj}')

            if _existing_obj:
                if all(
                    [
                        _existing_obj.__getattribute__(field) == value
                        for field, value in data.items()
                    ]
                ):
                    return _existing_obj

                logger.error('ObjectAlreadyExist exception occured.')
                raise ObjectAlreadyExist(
                    detail=self.already_exist_detail,
                    existing_object=_existing_obj,
                    serializer_class=self.__class__,
                )
        else:
            try:
                logger.debug('Method used: filter')
                _existing_obj = meta_model.objects.filter(**data).first()
            except TypeError:
                raise AssertionError(
                    'AlreadyExistHandler: Can not filter objects in '
                    '`get_existing_obj`. Make sure `many to many` related objects are '
                    'not passed or set `get_object` method to model instance, '
                    'specifying which fields to use in `Model.objects.get`.'
                )

        return None

    def create(self, validated_data: OrderedDict, *args, **kwargs) -> Type[Model]:
        """
        Check if there is already existing object with same data before create.
        Returns existing object if matches data, else run create.
        If existing object does not completely match data,
        ObjectAlreadyExist exception may be raised.
        """
        logger.debug(f'Check if object with passed data exist: {validated_data}')
        _existing_obj = self.check_existing_obj(validated_data)
        return (
            _existing_obj
            if _existing_obj
            else super().create(validated_data, *args, **kwargs)
        )

    def update(
        self, instance: Type[Model], validated_data: OrderedDict, *args, **kwargs
    ) -> Type[Model]:
        """
        Check if there is already existing object with same data
        that is not the current instance before update (avoid IntegrityError).
        If true, ObjectAlreadyExist custom exception is raised.
        """
        meta_model = self.Meta.model
        if hasattr(meta_model, 'get_object'):
            _existing_obj = meta_model.get_object(validated_data)
            if _existing_obj and instance != _existing_obj:
                try:
                    obj_lookup = _existing_obj.slug
                except AttributeError:
                    obj_lookup = _existing_obj.id
                raise ObjectAlreadyExist(
                    {'detail': self.already_exist_detail, 'obj_lookup': obj_lookup}
                )
        return super().update(instance, validated_data)


class AmountLimitsSerializerHandler:
    """
    Custom mixin to use in ModelSerializer.
    Adds `AmountLimitExceeded` custom exception handling.
    Required `amount_limits_check` Meta class attribute with objects list
    and its limits in format: objects_related_name: (amount_limit, detail_message).
    """

    amount_limit_exceeded_detail = AmountLimitExceeded.default_detail

    def validate(self, attrs: dict[str, Any]) -> OrderedDict:
        """Adds nested objects amount limit check."""
        if hasattr(self.Meta, 'amount_limits_check'):
            for objects_related_name, data in self.Meta.amount_limits_check.items():
                objects_data = attrs.get(objects_related_name, None)
                amount_limit, detail = data
                if objects_data and len(objects_data) > amount_limit:
                    raise AmountLimitExceeded(
                        detail=detail,
                        amount_limit=amount_limit,
                    )
        return super().validate(attrs)


class ListUpdateSerializer(serializers.ListSerializer):
    """
    Custom list serializer with implemented update method,
    IntegrityError handling (use when nested serializers is needed with
    NestedSerializerMixin for parent serializer).
    """

    def set_parent_data(self, data: list[OrderedDict], parent: Type[Model]) -> None:
        """
        This method is used to set data on the child objects from the parent object.
        There are 3 fields you can set on the meta class of the child serializer class:
        1. from_parent_fields: this field is the list of common fields between the parent
                               and child model. The values are copied from parent to child.
        2. generic_foreign_key: this field is tuple of object_id and content_type_id field.
        3. foreign_key_field_name: this field is the field name of the foriegn key of
                                   the parent model on the child model.
        `parent` param is the instance of the parent model.
        `data` is the list of dicts for the validated_data in the parent serializer.
        """
        meta = self.child.Meta
        for object_data in data:
            if hasattr(meta, 'from_parent_fields'):
                for field in meta.from_parent_fields:
                    if hasattr(parent, field):
                        object_data[field] = getattr(parent, field, None)
            if hasattr(meta, 'generic_foreign_key'):
                object_data[meta.generic_foreign_key[0]] = parent.pk
                object_data[
                    meta.generic_foreign_key[1]
                ] = ContentType.objects.get_for_model(parent)
            if hasattr(meta, 'foreign_key_field_name'):
                object_data[meta.foreign_key_field_name] = parent
            self.child.validate(attrs=object_data)

    def create(self, validated_data: OrderedDict) -> list[Type[Model]]:
        """
        Add update instead of create for objects with passed ids
        (to avoid IntegrityError for some passed nested objects).
        If invalid id passed, ObjectDoesNotExist exception may be raised.
        """
        child_objects = []
        for data in validated_data:
            if data.get('id', None):
                # perform update
                pk = data['id']
                other_args = {}
                author = data.get('author', None)
                if author:
                    other_args = {'author': author}
                obj = get_object_by_pk(self.child.Meta.model, pk, other_args=other_args)
                child_objects.append(self.child.update(obj, data))
            else:
                # perform create
                child_objects.append(self.child.create(data))
        return child_objects

    def update(
        self, instance: QuerySet, validated_data: OrderedDict
    ) -> list[Type[Model]]:
        """
        Add update for list of nested objects.
        Objects with passed ids, relations to which already exists, will be updated.
        Objects with passed ids, relations to which does not exist, will be updated
        and set to parent.
        Objects with no ids will be created and set to parent.
        Related objects which ids are missing will be deleted.
        If invalid id passed, ObjectDoesNotExist exception may be raised.
        """
        # Maps for id->instance and id->data item.
        obj_mapping = {obj.pk: obj for obj in instance}

        passed_pks = []

        # collect pks from passed data
        for data in validated_data:
            if data.get('id', None):
                pk = data['id']
                passed_pks.append(pk)

        if hasattr(self.child.Meta, 'foreign_key_field_name'):
            # Perform deletion of missing pks
            self.child.Meta.model.objects.filter(
                id__in=set(obj_mapping.keys()) - set(passed_pks)
            ).delete()

        child_objects = []
        for data in validated_data:
            if data.get('id', None):
                # perform update
                pk = data['id']
                other_args = {}
                author = data.get('author', None)
                if author:
                    other_args = {'author': author}
                obj = obj_mapping.get(
                    pk,
                    get_object_by_pk(self.child.Meta.model, pk, other_args=other_args),
                )
                child_objects.append(self.child.update(obj, data))
            else:
                # perform create
                child_objects.append(self.child.create(data))

        return child_objects


class NestedSerializerMixin(serializers.ModelSerializer):
    """
    Custom mixin to add create, update methods for nested serializers.
    If many=True is set for nested serializer, `list_serializer_class` Meta atribute
    of this nested serializer must be set to ListUpdateSerializer for update method to
    work correctly and handle IntegrityError.
    Also validates nested objects amount limits, if field name, amount limit are
    specified in `amount_limits_check` Meta atribute
    (format: {field_name: amount_limit}).
    """

    def create_child_objects(
        self,
        serializer: Type[serializers.BaseSerializer],
        data: OrderedDict,
        instance: Type[Model] | None = None,
    ) -> list[Type[Model]] | Type[Model]:
        """
        Create child object through its serializer.
        Set parent data if needed.
        """
        if isinstance(serializer, ListUpdateSerializer) and instance:
            serializer.set_parent_data(data, instance)
        return serializer.create(data)

    def set_child_data_to_instance(
        self,
        instance: Type[Model],
        nested_serializers_data: dict[str, Type[serializers.BaseSerializer]],
    ) -> None:
        """
        For each child data initialize the child serializer, set parent data
        using instance and create the child objects.
        Objects will be added through related manager if field name, related name are
        specified in `objs_related_names` Meta attribute
        (format: {field_name: related_name}).
        Use when parent instance must be created first.
        """
        for key, data in nested_serializers_data.items():
            serializer = self.get_fields()[key]
            self.set_child_context(
                serializer, 'request', self.context.get('request', None)
            )
            _child_obj = self.create_child_objects(serializer, data, instance=instance)
            if (
                hasattr(self.Meta, 'objs_related_names')
                and key in self.Meta.objs_related_names
            ):
                objs_related_names = self.Meta.objs_related_names.get(key)
                if serializer.many:
                    instance.__getattribute__(objs_related_names).add(*_child_obj)
                else:
                    instance.__getattribute__(objs_related_names).add(_child_obj)

    def set_child_data_to_validated_data(
        self,
        validated_data: OrderedDict,
        nested_serializers_data: dict[str, OrderedDict | list[OrderedDict]],
    ) -> None:
        """
        For each child data initialize the child serializer and create
        the child objects without passing instance
        (child object will be passed to validated_data).
        Use when child objects must be created first.
        """
        for key, data in nested_serializers_data.items():
            serializer = self.get_fields()[key]
            self.set_child_context(
                serializer, 'request', self.context.get('request', None)
            )
            _child_obj = self.create_child_objects(serializer, data)
            validated_data[key] = _child_obj
        return validated_data

    @staticmethod
    def set_child_context(
        child: type[serializers.BaseSerializer], context_attr: str, data: Any
    ) -> None:
        """Pass context to child serializer."""
        child.context[context_attr] = data

    @transaction.atomic
    def create(
        self, validated_data: OrderedDict, parent_first: bool = True
    ) -> Type[Model]:
        """Create parent instance and child objects."""
        nested_serializers_data = {}
        # find the child fields and remove the data from validated_data dict
        for key, val in self.get_fields().items():
            if isinstance(val, serializers.BaseSerializer) and not val.read_only:
                if val.source:
                    nested_serializers_data[key] = validated_data.pop(val.source, [])
                else:
                    nested_serializers_data[key] = validated_data.pop(key, [])
        if parent_first:
            # create instance then create the child objects
            instance = super().create(validated_data)
            self.set_child_data_to_instance(instance, nested_serializers_data)
        else:
            # create the child objects then create instance
            validated_data = self.set_child_data_to_validated_data(
                validated_data, nested_serializers_data
            )
            instance = super().create(validated_data)
        return instance

    @transaction.atomic
    def update(self, instance: Type[Model], validated_data: OrderedDict) -> Type[Model]:
        """Update parent instance and child objects."""
        nested_serializers_data = {}
        # find the child fields and remove the data from validated_data dict
        for key, val in self.get_fields().items():
            if isinstance(val, serializers.BaseSerializer) and not val.read_only:
                if val.source:
                    data = validated_data.pop(val.source, None)
                else:
                    data = validated_data.pop(key, None)
                if data is not None:
                    nested_serializers_data[key] = data
        # update instance then update the child objects
        instance = super().update(instance, validated_data)
        for key, data in nested_serializers_data.items():
            serializer = self.get_fields()[key]
            self.set_child_context(
                serializer, 'request', self.context.get('request', None)
            )
            key = serializer.source if serializer.source else key
            match serializer:
                case ListUpdateSerializer():
                    serializer.set_parent_data(data, instance)
                    _objs = serializer.update(getattr(instance, key).all(), data)
                    if (
                        hasattr(self.Meta, 'objs_related_names')
                        and key in self.Meta.objs_related_names
                    ):
                        objs_related_names = self.Meta.objs_related_names.get(key)
                        instance.__getattribute__(objs_related_names).set(_objs)
                case _:
                    _objs = [serializer.update(getattr(instance, key), data)]
        return instance


class FavoriteSerializerMixin(serializers.ModelSerializer):
    """
    Custom mixin to add `favorite` readable, writable field.
    `favorite_model`, `favorite_model_field` Meta attributes are required,
    where `favorite_model` is model with user, some favorite object fields,
    `favorite_model_field` is field name for some favorite object.
    """

    favorite = ReadWriteSerializerMethodField(
        method_name='get_favorite', required=False
    )

    def check_meta(self) -> None:
        assert hasattr(self.Meta, 'favorite_model'), (
            'Using FavoriteSerializerMixin requires `favorite_model` '
            'attribute to be set in Meta.'
        )
        assert hasattr(self.Meta, 'favorite_model_field'), (
            'Using FavoriteSerializerMixin requires `favorite_model_field` '
            'attribute to be set in Meta.'
        )
        return None

    def check_context(self) -> None:
        assert 'request' in self.context, (
            'FavoriteSerializerMixin: Providing `request` in context is required '
            'to get user.'
        )

    @extend_schema_field(serializers.BooleanField)
    def get_favorite(self, obj: Type[Model]) -> bool:
        """
        Returns True if there are user, favorite object in `favorite_model` objects,
        else False.
        For anonymous users always returns False.
        """
        self.check_meta()
        self.check_context()
        user = self.context['request'].user
        return (
            user.is_authenticated
            and self.Meta.favorite_model.objects.filter(
                **{self.Meta.favorite_model_field: obj}, user=user
            ).exists()
        )

    @transaction.atomic
    def create(self, validated_data: OrderedDict, *args, **kwargs) -> Type[Model]:
        """
        Add an object to favorites when creating it by passing the `favorite` field.
        """
        self.check_meta()
        self.check_context()
        favorite = validated_data.pop('favorite', None)
        instance = super().create(validated_data, *args, **kwargs)
        if favorite:
            self.Meta.favorite_model.objects.create(
                **{self.Meta.favorite_model_field: instance},
                user=self.context['request'].user,
            )
        return instance

    @transaction.atomic
    def update(self, instance: Type[Model], validated_data: OrderedDict) -> Type[Model]:
        """
        Add or remove an object from favorites when updating it by passing the
        `favorite` field.
        """
        self.check_meta()
        self.check_context()
        favorite = validated_data.pop('favorite', None)
        instance = super().update(instance, validated_data)
        current_favorite = self.Meta.favorite_model.objects.filter(
            **{self.Meta.favorite_model_field: instance},
            user=self.context['request'].user,
        )
        if favorite and not current_favorite:
            self.Meta.favorite_model.objects.create(
                **{self.Meta.favorite_model_field: instance},
                user=self.context['request'].user,
            )
        if not favorite and current_favorite:
            current_favorite.delete()
        return instance


class CountObjsSerializerMixin:
    """
    Custom mixin to add method for getting related objects amount.
    Using within KwargsMethodField (custom field from SerializerMethodField).
    `objs_related_name` keyword argument must be passed
    (related name for objects that need to be counted).
    """

    @extend_schema_field({'type': 'integer'})
    def get_objs_count(
        self, obj: Type[Model], objs_related_name: str = ''
    ) -> int | None:
        """
        Returns related objects amount or None if invalid `objs_related_name`
        was passed.
        """
        assert objs_related_name, '`objs_related_name` must be passed.'
        if hasattr(obj, objs_related_name):
            return obj.__getattribute__(objs_related_name).count()
        return None


class UpdateSerializerMixin:
    """
    Custom mixin to add update by passed pk within create method
    (to avoid IntegrityError when serializer is nested).
    """

    def create(
        self, validated_data: OrderedDict, parent_first: bool = True, *args, **kwargs
    ) -> Type[Model]:
        """Performs object update if object id is passed, else run create."""
        pk = validated_data.get('id', None)
        if pk:
            # perform update
            other_args = {}
            author = validated_data.get('author', None)
            if author:
                other_args = {'author': author}
            obj = get_object_by_pk(self.Meta.model, pk, other_args=other_args)
            return super().update(obj, validated_data, *args, **kwargs)
        # perform create
        return super().create(validated_data, *args, **kwargs)
