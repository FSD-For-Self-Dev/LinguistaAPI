"""Core serializer mixins."""

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from .serializers_fields import ReadWriteSerializerMethodField
from .exceptions import ObjectAlreadyExist, ObjectDoesNotExistWithDetail
from .constants import AmountLimits


class AlreadyExistSerializerHandler:
    """Миксин для обработки ошибки ObjectAlreadyExist или IntegrityError."""

    already_exist_detail = 'Object already exist.'

    def check_existing_obj(self, data, *args, **kwargs):
        meta_model = self.Meta.model
        if hasattr(meta_model, 'get_object'):
            _existing_obj = meta_model.get_object(data)
            if _existing_obj:
                if all(
                    [
                        _existing_obj.__getattribute__(field) == value
                        for field, value in data.items()
                    ]
                ):
                    return _existing_obj
                raise ObjectAlreadyExist(
                    detail=self.already_exist_detail,
                    existing_object=_existing_obj,
                    serializer_class=self.__class__,
                )
        else:
            try:
                _existing_obj = meta_model.objects.filter(**data).first()
            except TypeError:
                raise AssertionError(
                    'AlreadyExistHandler: Can not filter objects in '
                    '`get_existing_obj`. Make sure `many to many` related objects are '
                    'not passed or set `get_object` method to model instance, '
                    'specifying which fields to use in `Model.objects.get`.'
                )
        return None

    def create(self, validated_data, *args, **kwargs):
        """Check if there is already existing object with same data before create."""
        _existing_obj = self.check_existing_obj(validated_data)
        return (
            _existing_obj
            if _existing_obj
            else super().create(validated_data, *args, **kwargs)
        )

    def update(self, instance, validated_data, *args, **kwargs):
        """Check if there is other word with that data before update current."""
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


class ListUpdateSerializer(serializers.ListSerializer):
    """Сериализатор списка объектов с возможностью их обновления."""

    def set_parent_data(self, data, parent):
        """
        This method is used to set data on the child objects from the parent object
        There are 3. fields you can set on the meta class of the child serializer class:
        1. from_parent_fields: this field is the list of common fields between the parent
                               and child model. The values are copied from parent to child
        2. generic_foreign_key: this field is tuple of object_id and content_type_id field
        3. foreign_key_field_name: this field is the field name of the foriegn key of the parent model on the child model
        parent param is the instance of the parent model
        data is the list of dicts for the validated_data in the parent serializer
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

    def create(self, validated_data):
        ret = []
        for data in validated_data:
            if data.get('id', None):
                pk = data['id']
                try:
                    author = data.get('author', None)
                    obj = (
                        self.child.Meta.model.objects.get(pk=pk, author=author)
                        if author
                        else self.Meta.model.objects.get(pk=pk)
                    )
                    ret.append(self.child.update(obj, data))
                except ObjectDoesNotExist:
                    obj_name = self.child.Meta.model._meta.verbose_name
                    raise ObjectDoesNotExistWithDetail(
                        detail=f'{obj_name} с id={pk} не найден.',
                        code=f'{self.child.Meta.model}_object_not_exist',
                    )
            else:
                ret.append(self.child.create(data))
        return ret

    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        obj_mapping = {obj.pk: obj for obj in instance}

        existing_pks = []
        ret = []

        # find existing pks
        for data in validated_data:
            if data.get('id', None):
                pk = data['id']
                existing_pks.append(pk)

        if hasattr(self.child.Meta, 'foreign_key_field_name'):
            # Perform deletion of missing pks
            self.child.Meta.model.objects.filter(
                id__in=set(obj_mapping.keys()) - set(existing_pks)
            ).delete()

        for data in validated_data:
            if data.get('id', None):
                # perform update
                pk = data['id']
                if pk in obj_mapping:
                    obj = obj_mapping[pk]
                else:
                    try:
                        author = data.get('author', None)
                        obj = (
                            self.child.Meta.model.objects.get(pk=pk, author=author)
                            if author
                            else self.Meta.model.objects.get(pk=pk)
                        )
                    except ObjectDoesNotExist:
                        obj_name = self.child.Meta.model._meta.verbose_name
                        raise ObjectDoesNotExistWithDetail(
                            detail=f'{obj_name} с id={pk} не найден.',
                            code=f'{self.child.Meta.model}_object_not_exist',
                        )
                ret.append(self.child.update(obj, data))
            else:
                # perform create
                ret.append(self.child.create(data))

        return ret


class NestedSerializerMixin(serializers.ModelSerializer):
    """Миксин для обработки вложенных сериализаторов."""

    def validate(self, attrs):
        # Валидация максимального количества элементов вложенного сериализатора
        if hasattr(self.Meta, 'amount_limit_fields'):
            for field_name, limit in self.Meta.amount_limit_fields.items():
                obj_list = attrs.get(field_name, None)
                if obj_list and len(obj_list) > limit:
                    raise serializers.ValidationError(
                        _(
                            AmountLimits.get_error_message(
                                limit,
                                attr_name=self.Meta.model._meta.verbose_name_plural,
                            )
                        )
                    )
        return super().validate(attrs)

    def create_child_objects(self, serializer, data, instance=None):
        if isinstance(serializer, ListUpdateSerializer) and instance:
            serializer.set_parent_data(data, instance)
        return serializer.create(data)

    def set_child_data_to_instance(self, instance, nested_serializers_data):
        """
        For each child data initialize the child list serializer, set parent data
        using instance and create the child objects.
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

    def set_child_data_to_validated_data(self, validated_data, nested_serializers_data):
        """
        For each child data initialize the child list serializer and create
        the child objects without passing instance.
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
    def set_child_context(child, context_attr, data):
        child.context[context_attr] = data

    @transaction.atomic
    def create(self, validated_data, parent_first=True):
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
    def update(self, instance, validated_data):
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
    """Миксин для добавления записи и чтения поля `favorite`."""

    favorite = ReadWriteSerializerMethodField(
        method_name='get_favorite', required=False
    )

    def check_meta(self):
        assert hasattr(self.Meta, 'favorite_model'), (
            'Using FavoriteSerializerMixin requires `favorite_model` '
            'attribute to be set in Meta.'
        )
        assert hasattr(self.Meta, 'favorite_model_field'), (
            'Using FavoriteSerializerMixin requires `favorite_model_field` '
            'attribute to be set in Meta.'
        )
        return None

    @extend_schema_field(serializers.BooleanField)
    def get_favorite(self, obj):
        self.check_meta()
        # check context is needed
        user = self.context['request'].user
        return (
            user.is_authenticated
            and self.Meta.favorite_model.objects.filter(
                **{self.Meta.favorite_model_field: obj}, user=user
            ).exists()
        )

    @transaction.atomic
    def create(self, validated_data, *args, **kwargs):
        self.check_meta()
        favorite = validated_data.pop('favorite', None)
        instance = super().create(validated_data, *args, **kwargs)
        if favorite:
            self.Meta.favorite_model.objects.create(
                **{self.Meta.favorite_model_field: instance},
                user=self.context['request'].user,
            )
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        self.check_meta()
        favorite = validated_data.pop('favorite', None)
        instance = super().update(instance, validated_data)
        filter_favorite = self.Meta.favorite_model.objects.filter(
            **{self.Meta.favorite_model_field: instance},
            user=self.context['request'].user,
        )
        if favorite and not filter_favorite:
            self.Meta.favorite_model.objects.create(
                **{self.Meta.favorite_model_field: instance},
                user=self.context['request'].user,
            )
        if not favorite and filter_favorite:
            filter_favorite.delete()
        return instance


class CountObjsSerializerMixin:
    """Миксин для чтения счетчика связанных объектов."""

    @extend_schema_field({'type': 'integer'})
    def get_objs_count(self, obj, objs_related_name=''):
        assert objs_related_name, '`objs_related_name` must be passed.'
        if hasattr(obj, objs_related_name):
            return obj.__getattribute__(objs_related_name).count()
        return None


class UpdateSerializerMixin:
    """Миксин для обновления объекта при создании."""

    def create(self, validated_data, parent_first=True, *args, **kwargs):
        pk = validated_data.get('id', None)
        author = validated_data.get('author', None)
        if pk:
            try:
                instance = (
                    self.Meta.model.objects.get(pk=pk, author=author)
                    if author
                    else self.Meta.model.objects.get(pk=pk)
                )
                return self.update(instance, validated_data)
            except ObjectDoesNotExist:
                raise ObjectDoesNotExistWithDetail(
                    detail=f'{self.Meta.model._meta.verbose_name} с id={pk} не найдено в вашем словаре.',
                    code=f'{self.Meta.model.__name__}_object_not_exist',
                )
        return super().create(validated_data, *args, **kwargs)
