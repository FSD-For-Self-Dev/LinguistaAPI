import operator
from functools import reduce

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _
from django.db.models import Q

from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

from core.exceptions import AmountLimitExceeded, ObjectAlreadyExist
from core.constants import AmountLimits


class ActionsWithRelatedObjectsMixin:
    def list_related_objs(
        self,
        request,
        objs_related_name='',
        status_code=status.HTTP_200_OK,
        search_fields=[],
        *args,
        **kwargs,
    ):
        """Осуществить метод list для связанных объектов."""
        _objs = kwargs.get('objs', None)
        if _objs is None:
            instance = self.get_object()
            if search_fields:
                orm_lookups = [
                    '__'.join([str(search_field), 'regex'])
                    for search_field in search_fields
                ]
                search_term = request.query_params.get('search', '')
                queries = [Q(**{orm_lookup: search_term}) for orm_lookup in orm_lookups]
                _objs = instance.__getattribute__(objs_related_name).filter(
                    (reduce(operator.or_, queries))
                )
            else:
                _objs = instance.__getattribute__(objs_related_name).all()
        serializer_class = kwargs.get('serializer_class', None)
        serializer_class = (
            serializer_class if serializer_class else self.get_serializer_class()
        )
        serializer = serializer_class(_objs, many=True, context={'request': request})
        response_objs_name = kwargs.get('response_objs_name', objs_related_name)
        return Response(
            {
                'count': _objs.count(),
                **kwargs.get('extra_data', {}),
                response_objs_name: serializer.data if _objs else [],
            },
            status=status_code,
        )

    def paginate_related_objs(
        self, request, objs, objs_serializer_class=None, *args, **kwargs
    ):
        page = self.paginate_queryset(objs)
        if page is not None:
            serializer = (
                objs_serializer_class(page, many=True, context={'request': request})
                if objs_serializer_class
                else self.get_serializer(page, many=True)
            )
            return self.get_paginated_response(serializer.data).data

        serializer = (
            objs_serializer_class(objs, many=True, context={'request': request})
            if objs_serializer_class
            else self.get_serializer(objs, many=True)
        )
        return serializer.data

    def get_filtered_paginated_objs(self, request, objs, view, serializer_class):
        for backend in view.filter_backends:
            objs = backend().filter_queryset(request, objs, view)

        paginator = view.pagination_class()
        _objs_paginated = paginator.paginate_queryset(objs, request, self)
        _objs_serializer_data = serializer_class(
            _objs_paginated, many=True, context={'request': request}
        ).data
        return paginator.get_paginated_response(_objs_serializer_data).data

    @transaction.atomic
    def create_related_objs(
        self,
        request,
        objs_related_name,
        amount_limit=None,
        related_model=None,
        set_objs=False,
        return_objs_list=False,
        instance=None,
        serializer=None,
        *args,
        **kwargs,
    ):
        """Осуществить метод create для связанных объектов."""
        instance = instance if instance else self.get_object()
        serializer = (
            serializer(data=request.data, many=True, context={'request': request})
            if serializer
            else self.get_serializer(data=request.data, many=True)
        )
        serializer.is_valid(raise_exception=True)

        # Validate objs amount limit
        if amount_limit:
            existing_objs_amount = instance.__getattribute__(objs_related_name).count()
            new_objs_amount = len(serializer.validated_data)
            if existing_objs_amount + new_objs_amount > amount_limit:
                attr_name = (
                    related_model._meta.verbose_name_plural
                    if related_model
                    else objs_related_name
                )
                raise AmountLimitExceeded(
                    detail=AmountLimits.get_error_message(
                        amount_limit, attr_name=attr_name
                    )
                )

        try:
            _new_objs = serializer.save()

            # Set related objs if needed
            if set_objs:
                instance.__getattribute__(objs_related_name).add(
                    *_new_objs, through_defaults=kwargs.get('through_defaults', None)
                )

            response_objs_name = kwargs.get('response_objs_name', objs_related_name)
            if return_objs_list:
                return self.list_related_objs(
                    request,
                    objs_related_name,
                    status_code=status.HTTP_201_CREATED,
                    response_objs_name=response_objs_name,
                    serializer_class=kwargs.get('response_serializer', None),
                )
            response_serializer = kwargs.get('response_serializer', None)
            instance_serializer = (
                response_serializer(instance, context={'request': request})
                if response_serializer
                else self.get_serializer(instance)
            )
            return Response(
                instance_serializer.data,
                status=status.HTTP_201_CREATED,
            )
        except ObjectAlreadyExist as exception:
            return exception.get_detail_response(request)

    @transaction.atomic
    def detail_action(
        self,
        request,
        objs_related_name,
        lookup_attr_name,
        lookup_field='pk',
        *args,
        **kwargs,
    ):
        """Осуществить методы retrieve, partial_update, destroy для связанных объектов."""
        instance = self.get_object()
        try:
            _obj = instance.__getattribute__(objs_related_name).get(
                **{lookup_field: kwargs.get(lookup_attr_name)}
            )
        except ObjectDoesNotExist:
            raise NotFound

        match request.method:
            case 'GET':
                return Response(
                    self.get_serializer(_obj).data, status=status.HTTP_200_OK
                )
            case 'PATCH':
                serializer = self.get_serializer(
                    instance=_obj, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                try:
                    serializer.save()
                except ObjectAlreadyExist as exception:
                    return exception.get_detail_response(request)
                return Response(serializer.data, status=status.HTTP_200_OK)
            case 'DELETE':
                delete_through_manager = kwargs.get('delete_through_manager', False)
                if delete_through_manager:
                    instance.__getattribute__(objs_related_name).remove(_obj)
                else:
                    _obj.delete()
                objs_related_name = kwargs.get(
                    'list_objs_related_name', objs_related_name
                )
                response_objs_name = kwargs.get('response_objs_name', objs_related_name)
                return self.list_related_objs(
                    request,
                    objs_related_name,
                    status_code=status.HTTP_204_NO_CONTENT,
                    response_objs_name=response_objs_name,
                    serializer_class=kwargs.get('list_serializer', None),
                )


class ObjectAlreadyExistHandler:
    def create(self, request, *args, **kwargs):
        """Обработать ошибку ObjectAlreadyExist перед созданием объекта."""
        try:
            return super().create(request, *args, **kwargs)
        except ObjectAlreadyExist as exception:
            return exception.get_detail_response(request)

    def update(self, request, *args, **kwargs):
        """Обработать ошибку ObjectAlreadyExist перед обновлением объекта."""
        try:
            return super().update(request, *args, **kwargs)
        except ObjectAlreadyExist as exception:
            return exception.get_detail_response(request)


class DestroyReturnListMixin:
    def destroy(self, request, *args, **kwargs):
        """Возвращать обновленный список объектов после удаления объекта."""
        instance = self.get_object()
        self.perform_destroy(instance)
        list_response_data = self.list(request).data
        return Response(list_response_data, status=status.HTTP_204_NO_CONTENT)


class FavoriteMixin:
    def _add_to_favorite_action(
        self,
        request,
        related_model,
        related_model_obj_field,
        already_exist_msg='Object already in favorites.',
    ):
        """Добавить объект в избранное."""
        obj = self.get_object()
        __, created = related_model.objects.get_or_create(
            **{related_model_obj_field: obj, 'user': request.user}
        )
        if not created:
            return Response(
                {'detail': _(already_exist_msg)},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = self.get_serializer(obj, many=False, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_favorite_action(
        self,
        request,
        related_model,
        related_model_obj_field,
        not_found_msg='Object not found.',
    ):
        """Удалить объект из избранного."""
        obj = self.get_object()
        deleted, __ = related_model.objects.filter(
            **{related_model_obj_field: obj, 'user': request.user}
        ).delete()
        if not deleted:
            return Response(
                {'detail': _(not_found_msg)},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.get_serializer(obj, many=False, context={'request': request})
        return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
