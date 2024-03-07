from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _

from rest_framework import serializers
from rest_framework.fields import empty
from drf_spectacular.utils import extend_schema_field

from .serializers_fields import ReadWriteSerializerMethodField
from .exceptions import ObjectAlreadyExist, ObjectDoesNotExistWithDetail
from .constants import AmountLimits


class AlreadyExistSerializerHandler(serializers.ModelSerializer):
    already_exist_detail = 'Object already exist.'

    def get_existing_obj(self, data, *args, **kwargs):
        meta_model = self.Meta.model
        if hasattr(meta_model, 'get_object'):
            _existing_obj = meta_model.get_object(data)
        else:
            try:
                _existing_obj = meta_model.objects.filter(**data).first()
            except TypeError:
                raise AssertionError(
                    'AlreadyExistHandler: Can not filter objects in '
                    '`get_existing_obj`. Make sure foreign keys passed as int() or '
                    'set `get_object` method to model instance, specifying which '
                    'fields to use in `Model.objects.get`.'
                )
        return _existing_obj if _existing_obj else None

    def create(self, validated_data, *args, **kwargs):
        _existing_obj = self.get_existing_obj(validated_data)
        if _existing_obj:
            raise ObjectAlreadyExist(
                detail=self.already_exist_detail,
                existing_object=_existing_obj,
                serializer_class=self.__class__,
            )
        return super().create(validated_data, *args, **kwargs)


class ListUpdateSerializer(serializers.ListSerializer):
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

    def get_or_create(self, validated_data):
        _objs = []
        _conflicts = []
        meta_model = self.child.Meta.model
        for attrs in validated_data:
            if isinstance(self.child, NestedSerializerMixin):
                _objs.append(self.child.create(attrs))
                if self.child.nested_conflict_data:
                    _conflicts.append(self.child.nested_conflict_data)
                continue
            _existing_obj = meta_model.objects.filter(**attrs).first()
            if _existing_obj:
                _objs.append(_existing_obj)
                continue
            elif hasattr(meta_model, 'get_object'):
                _existing_obj = meta_model.get_object(attrs)
                if _existing_obj:
                    _objs.append(_existing_obj)
                    _conflicts.append(
                        {
                            'passed_data': self.child.__class__(attrs).data,
                            'existing_data': self.child.__class__(_existing_obj).data,
                        }
                    )
                    continue
            _objs.append(self.child.create(attrs))
        return (_objs, _conflicts)

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
                        obj = self.child.Meta.model.objects.get(pk=pk)
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
    def __init__(self, instance=None, data=empty, **kwargs):
        self.nested_conflict_data = {}
        super().__init__(instance, data, **kwargs)

    @staticmethod
    def check_max_amount(obj_list, limit, attr_name):
        """Статический метод для валидации максимального количества элементов
        вложенного сериализатора."""
        if len(obj_list) > limit:
            raise serializers.ValidationError(
                {attr_name: _(AmountLimits.get_error_message(limit))}
            )

    def validate(self, attrs):
        if hasattr(self.Meta, 'amount_limit_fields'):
            for attr_name, limit in self.Meta.amount_limit_fields.items():
                attr = attrs.get(attr_name, None)
                if attr:
                    self.check_max_amount(attr, limit, attr_name)
        return super().validate(attrs)

    def get_or_create_child_objects(self, serializer, data, field_name, instance=None):
        match serializer:
            case ListUpdateSerializer():
                if instance:
                    serializer.set_parent_data(data, instance)
                _obj, _conflicts = serializer.get_or_create(data)
                if _conflicts:
                    self.nested_conflict_data[field_name] = _conflicts
            case NestedSerializerMixin():
                _obj = serializer.create(data)
                if serializer.nested_conflict_data:
                    self.nested_conflict_data[
                        field_name
                    ] = serializer.nested_conflict_data
            case serializers.ModelSerializer():
                meta_model = serializer.Meta.model
                _obj = meta_model.objects.filter(**data).first()
                if not _obj and hasattr(meta_model, 'get_object'):
                    _obj = meta_model.get_object(data)
                    if _obj:
                        _conflicts.append(
                            {
                                'passed_data': serializer.__class__(data).data,
                                'existing_data': serializer.__class__(_obj).data,
                            }
                        )
                    else:
                        _obj = serializer.create(data)
            case _:
                _obj = serializer.create(data)
        return _obj

    def set_child_data_to_instance(self, instance, nested_serializers_data):
        """
        For each child data initialize the child list serializer, set parent data
        using instance and create the child objects.
        """
        for key, data in nested_serializers_data.items():
            serializer = self.get_fields()[key]
            _child_obj = self.get_or_create_child_objects(
                serializer, data, key, instance
            )
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
            _child_obj = self.get_or_create_child_objects(serializer, data, key)
            validated_data[key] = _child_obj
        return validated_data

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
        for key, val in self.get_fields().items():
            if isinstance(val, serializers.BaseSerializer) and not val.read_only:
                if val.source:
                    data = validated_data.pop(val.source, [])
                else:
                    data = validated_data.pop(key, [])
                if data:
                    nested_serializers_data[key] = data
        instance = super().update(instance, validated_data)
        for key, data in nested_serializers_data.items():
            serializer = self.get_fields()[key]
            match serializer:
                case ListUpdateSerializer():
                    serializer.set_parent_data(data, instance)
                    if serializer.source:
                        _objs = serializer.update(
                            getattr(instance, serializer.source).all(), data
                        )
                    else:
                        _objs = serializer.update(getattr(instance, key).all(), data)
                    if (
                        hasattr(self.Meta, 'objs_related_names')
                        and key in self.Meta.objs_related_names
                    ):
                        objs_related_names = self.Meta.objs_related_names.get(key)
                        instance.__getattribute__(objs_related_names).set(_objs)
                case _:
                    _objs = [
                        serializer.update(getattr(instance, key), data),
                    ]
        return instance


class FavoriteSerializerMixin(serializers.ModelSerializer):
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
        return self.Meta.favorite_model.objects.filter(
            **{self.Meta.favorite_model_field: obj}, user=self.context['request'].user
        ).exists()

    @transaction.atomic
    def create(self, validated_data):
        self.check_meta()
        favorite = validated_data.pop('favorite', None)
        instance = super().create(validated_data)
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


class CountObjsSerializerMixin(serializers.ModelSerializer):
    @extend_schema_field({'type': 'integer'})
    def get_objs_count(self, obj, objs_related_name=''):
        assert objs_related_name, '`objs_related_name` must be passed.'
        if hasattr(obj, objs_related_name):
            return obj.__getattribute__(objs_related_name).count()
        return None


class UpdateSerializerMixin:
    def create(self, validated_data, parent_first=True):
        if 'id' in validated_data:
            instance = self.Meta.model.objects.get(pk=validated_data.pop('id'))
            return super().update(instance, validated_data)
        return super().create(validated_data)
