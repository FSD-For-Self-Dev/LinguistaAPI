"""API views mixins."""

import operator
import logging
from functools import reduce
from typing import Type

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _
from django.db.models import Q, Model
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse

from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.utils.serializer_helpers import ReturnDict
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from api.v1.core.exceptions import ObjectAlreadyExist, AmountLimitExceeded
from utils.checkers import check_amount_limit

logger = logging.getLogger(__name__)


class ObjectAlreadyExistHandler:
    """Custom mixin to add custom ObjectAlreadyExist exception handling."""

    def create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle ObjectAlreadyExist exception defore creating."""
        try:
            return super().create(request, *args, **kwargs)
        except ObjectAlreadyExist as exception:
            logger.error(f'ObjectAlreadyExist exception occured: {exception}')
            return exception.get_detail_response(request)

    def update(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle ObjectAlreadyExist exception defore updating."""
        try:
            return super().update(request, *args, **kwargs)
        except ObjectAlreadyExist as exception:
            logger.error(f'ObjectAlreadyExist exception occured: {exception}')
            return exception.get_detail_response(request)


class AmountLimitExceededHandler:
    """Custom mixin to add custom AmountLimitExceeded exception handling."""

    def create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle AmountLimitExceeded exception defore creating."""
        try:
            return super().create(request, *args, **kwargs)
        except AmountLimitExceeded as exception:
            logger.error(f'AmountLimitExceeded exception occured: {exception}')
            return exception.get_detail_response(request)

    def update(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle AmountLimitExceeded exception defore updating."""
        try:
            return super().update(request, *args, **kwargs)
        except AmountLimitExceeded as exception:
            logger.error(f'AmountLimitExceeded exception occured: {exception}')
            return exception.get_detail_response(request)


class ActionsWithRelatedObjectsMixin:
    """Custom mixin to add actions with related objects."""

    def list_related_objs(
        self,
        request: HttpRequest,
        objs_related_name: str = '',
        objs: QuerySet | None = None,
        serializer_class: Serializer | None = None,
        status_code: int = status.HTTP_200_OK,
        response_extra_data: dict = {},
        response_objs_name: str = '',
        search_fields: list[str] = [],
        *args,
        **kwargs,
    ) -> HttpResponse:
        """
        Returns all related objects.
        Returns filtered objects if `search_fields` is passed.

        Args:
            objs_related_name (str): objects related name, use to get objects from
                                     related instance.
            objs (QuerySet): related objects that need to be returned,
                             default None, obtains from related manager,
                             pass `objs` if they are already obtained to
                             optimize script.
            serializer_class (Serializer subclass): serializer class to be used for listing
                                           objects.
            status_code (int): http status that need to be returned in response.
            response_extra_data (dict): extra data to be returned in response.
            response_objs_name (str): objects name to be returned in response,
                                      uses objs_related_name if not passed.
            search_fields (list[str]): enables searching for listing objects,
                                       accepts list of fields used to search
                                       (filtering) objects.
        """
        logger.debug(f'Obtaining list of related objects: {objs_related_name}')

        # Obtaining objects if not passed
        if objs is None:
            instance = self.get_object()
            logger.debug(f'Obtained instance: {instance}')

            # Filtering objects by 'regex' lookup if search_fileds passed
            if search_fields:
                orm_lookups = [
                    '__'.join([str(search_field), 'regex'])
                    for search_field in search_fields
                ]
                search_term = request.query_params.get('search', '')
                queries = [Q(**{orm_lookup: search_term}) for orm_lookup in orm_lookups]
                objs = instance.__getattribute__(objs_related_name).filter(
                    (reduce(operator.or_, queries))
                )
            else:
                objs = instance.__getattribute__(objs_related_name).all()

        logger.debug(f'Obtained objects: {objs}')

        serializer_class = (
            serializer_class if serializer_class else self.get_serializer_class()
        )
        logger.debug(f'Serializer used: {serializer_class}')

        serializer = serializer_class(objs, many=True, context={'request': request})
        return Response(
            {
                'count': objs.count(),
                **response_extra_data,
                response_objs_name or objs_related_name: serializer.data
                if objs
                else [],
            },
            status=status_code,
        )

    def paginate_related_objs(
        self,
        request: HttpRequest,
        objs: QuerySet,
        serializer_class: Serializer | None = None,
        *args,
        **kwargs,
    ) -> ReturnDict:
        """
        Returns paginated related objects if pagination is unabled.

        Args:
            objs (QuerySet): related objects that need to be filtered or paginated.
            serializer_class (Serializer subclass): serializer class to represent
                                                    objects list, obtained from
                                                    self.get_serializer() if not
                                                    passed.
        """
        logger.debug('Paginating objects')
        page = self.paginate_queryset(objs)

        serializer = (
            serializer_class(page or objs, many=True, context={'request': request})
            if serializer_class
            else self.get_serializer(page or objs, many=True)
        )

        if page:
            logger.debug('Returning paginated response data')
            return self.get_paginated_response(serializer.data).data

        return serializer.data

    def get_filtered_paginated_objs(
        self,
        request: HttpRequest,
        objs: QuerySet,
        view: GenericViewSet,
        serializer_class: Serializer,
    ) -> ReturnDict:
        """
        Returns filtered, paginated related objects,
        uses passed view filter_backends, pagination_class attributes.

        Args:
            objs (QuerySet): related objects that need to be filtered or paginated.
            view (GenericViewSet subclass): view that will be used to filter and
                                            paginate related objects.
            serializer_class (Serializer subclass): serializer class to represent
                                                    objects list.
        """
        logger.debug(
            f'Filtering related objects with filter backends: {view.filter_backends}'
        )
        for backend in view.filter_backends:
            objs = backend().filter_queryset(request, objs, view)

        paginator = view.pagination_class()
        logger.debug(
            f'Paginating related objects with pagination class: {type(paginator)}'
        )
        page = paginator.paginate_queryset(objs, request, self)

        _objs_serializer_data = serializer_class(
            page or objs, many=True, context={'request': request}
        ).data

        if page is not None:
            logger.debug('Returning paginated response data')
            return paginator.get_paginated_response(_objs_serializer_data).data

        return _objs_serializer_data

    @transaction.atomic
    def create_related_objs(
        self,
        request: HttpRequest,
        objs_related_name: str,
        amount_limit: int | None = None,
        set_objs: bool = False,
        return_objs_list: bool = False,
        instance: Type[Model] | None = None,
        serializer_class: Serializer | None = None,
        response_serializer_class: Serializer | None = None,
        response_objs_name: str = '',
        amount_limit_exceeded_detail: str = AmountLimitExceeded.default_detail,
        *args,
        **kwargs,
    ) -> HttpResponse:
        """
        Creates related objects.
        Returns list of all related objects if `return_objs_list` set True,
        else returns related instance data.
        Validated related objects amount limits, custom AmountLimitExceeded exception
        may be raised.

        Args:
            objs_related_name (str): objects related name, use to validate amount
                                     limit, set objects to related instance
                                     (in case `set_objs` is True), return all related
                                     objects list (in case `return_objs_list` is True).
            amount_limit (int): the maximum possible objects amount, use to validate
                                amount limit, default None.
            set_objs (bool): set True if objects need to be set through related
                             manager after save (you may pass `through_defaults`
                             in kwargs), default False.
            return_objs_list (bool): set True if response needs to return a list of
                                     all related objects, including those created,
                                     default False (`response_objs_name` may be pass
                                     through kwargs to change objects name in reponse).
            instance (Model subclass): instance to which objects relate,
                                       default None, obtains from
                                       `self.get_object()`, pass instance if
                                       it is already obtained to optimize
                                       script.
            serializer_class (Serializer subclass): related objects serializer class,
                                              use to create objects,
                                              obtain from self.get_serializer() if
                                              None, default None.
            response_serializer_class (Serializer subclass): related objects list
                                                       serializer class, use to return
                                                       all related objects list if
                                                       `return_objs_list` set True,
                                                       or related instace serializer
                                                       class, use to return instance data,
                                                       obtain from
                                                       self.get_serializer() if None,
                                                       default None.
            response_objs_name (str): objects name to be returned in response,
                                      uses objs_related_name if not passed.
            amount_limit_exceeded_detail (str): detail message if AmountLimitExceeded
                                                exception was raised.

        """
        logger.debug(f'Creating related objects: {objs_related_name}')

        instance = instance if instance else self.get_object()
        logger.debug(f'Related instance: {instance}')

        serializer = (
            serializer_class(data=request.data, many=True, context={'request': request})
            if serializer_class
            else self.get_serializer(data=request.data, many=True)
        )
        logger.debug(f'Serializer used to create related objects: {type(serializer)}')

        logger.debug(f'Validating data: {request.data}')
        serializer.is_valid(raise_exception=True)

        # Validate objects amount limits if `amount_limit` is passed
        if amount_limit:
            logger.debug('Checking amount limits')
            try:
                check_amount_limit(
                    current_amount=instance.__getattribute__(objs_related_name).count(),
                    new_objects_amount=len(serializer.validated_data),
                    amount_limit=amount_limit,
                    detail=amount_limit_exceeded_detail,
                )
            except AmountLimitExceeded as exception:
                return exception.get_detail_response(request)

        try:
            logger.debug('Performing save')
            _new_objs = serializer.save()

            # Set related objects throught related manager if needed
            if set_objs:
                logger.debug(
                    'Setting new related objects to instance through related manager'
                )
                instance.__getattribute__(objs_related_name).add(
                    *_new_objs, through_defaults=kwargs.get('through_defaults', None)
                )

            # Return all related objects list instead of instance data if needed
            if return_objs_list:
                logger.debug('Returning all related objects list')
                return self.list_related_objs(
                    request,
                    objs_related_name,
                    status_code=status.HTTP_201_CREATED,
                    response_objs_name=response_objs_name or objs_related_name,
                    serializer_class=response_serializer_class,
                )

            # Return instance data
            logger.debug('Returning instance data')
            instance_serializer = (
                response_serializer_class(instance, context={'request': request})
                if response_serializer_class
                else self.get_serializer(instance)
            )
            return Response(
                instance_serializer.data,
                status=status.HTTP_201_CREATED,
            )

        except ObjectAlreadyExist as exception:
            logger.error(f'ObjectAlreadyExist exception occured: {exception}')
            return exception.get_detail_response(request)

    @transaction.atomic
    def detail_action(
        self,
        request: HttpRequest,
        objs_related_name: str,
        lookup_query_param: str,
        lookup_field: str = 'pk',
        delete_through_manager: bool = False,
        delete_return_list: bool = True,
        response_objs_name: str = '',
        response_serializer_class: Serializer | None = None,
        *args,
        **kwargs,
    ) -> HttpResponse:
        """
        Related objects retrieve, partial_update, destroy actions.

        Args:
            objs_related_name (str): objects related name, use to get objects from
                                     related instance.
            lookup_query_param (str): lookup field name parameter passed in url_path to
                                    get object.
            lookup_field (str): lookup field, which url_path parameter value
                                passed to, to get object.
            delete_through_manager (bool): set True if object needs to be deleted only
                                           from instance through related manager
                                           instead of deleting object itself,
                                           default False.
            delete_return_list (bool): return all remains objects list if True,
                                       default True.
            response_objs_name (str): objects name to be returned in response,
                                      uses objs_related_name if not passed.
            response_serializer_class (Serializer subclass): serializer class to return all
                                                   related objects list after some
                                                   object delete, obtains from
                                                   self.get_serializer_class()
                                                   if None, default None.
        """
        instance = self.get_object()
        logger.debug(f'Obtained instance: {instance}')

        # Try to get related object through lookup field, NotFound may be raised.
        try:
            logger.debug(
                f'Lookup field: {lookup_field}, '
                f'Lookup query param: {lookup_query_param}, '
                f'Objects related name: {objs_related_name}'
            )
            _obj = instance.__getattribute__(objs_related_name).get(
                **{lookup_field: kwargs.get(lookup_query_param)}
            )
            logger.debug(f'Obtained object: {_obj}')
        except ObjectDoesNotExist as exception:
            logger.error(f'ObjectDoesNotExist exception occured: {exception}')
            raise NotFound

        match request.method:
            case 'GET':
                logger.debug('Retrieving object')
                return Response(
                    self.get_serializer(_obj).data, status=status.HTTP_200_OK
                )

            case 'PATCH':
                logger.debug('Updating object')

                serializer = self.get_serializer(
                    instance=_obj, data=request.data, partial=True
                )
                logger.debug(f'Serializer used: {type(serializer)}')

                logger.debug('Validating data')
                serializer.is_valid(raise_exception=True)

                # Custom ObjectAlreadyExist exception handling
                try:
                    logger.debug('Performing save')
                    serializer.save()
                except ObjectAlreadyExist as exception:
                    logger.error(f'ObjectAlreadyExist exception occured: {exception}')
                    return exception.get_detail_response(request)

                return Response(serializer.data, status=status.HTTP_200_OK)

            case 'DELETE':
                # Delete object from instance or delete object itself
                if delete_through_manager:
                    logger.debug(
                        'Deleting object through related manager '
                        '(disassociate object with instance)'
                    )
                    instance.__getattribute__(objs_related_name).remove(_obj)
                else:
                    logger.debug('Deleting object')
                    _obj.delete()

                # Return all remains objects list
                if delete_return_list:
                    logger.debug('Returning all related objects list')
                    return self.list_related_objs(
                        request,
                        objs_related_name,
                        status_code=status.HTTP_200_OK,
                        response_objs_name=response_objs_name or objs_related_name,
                        serializer_class=response_serializer_class,
                    )

                logger.debug('Returning no data')
                return Response(status=status.HTTP_204_NO_CONTENT)


class DestroyReturnListMixin:
    """Custom mixin to return remain objects list after deleting current object."""

    def destroy(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Delete object, return all remain objects list."""
        instance = self.get_object()
        logger.debug(f'Obtained instance: {instance}')

        logger.debug('Performing instance destroy')
        self.perform_destroy(instance)

        logger.debug('Obtaining remain objects list')
        list_response_data = self.list(request).data

        return Response(list_response_data, status=status.HTTP_200_OK)


class FavoriteMixin:
    """Custom mixin to add actions with favorite objects."""

    def _add_to_favorite_action(
        self,
        request: HttpRequest,
        related_model: Model,
        related_model_obj_field: str,
        already_exist_msg: str = 'Object already in favorites.',
    ) -> HttpResponse:
        """Add object to favorites. Returns object data."""
        obj = self.get_object()
        logger.debug(f'Obtained object: {obj}')

        logger.debug('Adding object to users favorites')
        logger.debug(f'Model used: {related_model}')
        __, created = related_model.objects.get_or_create(
            **{related_model_obj_field: obj, 'user': request.user}
        )

        if not created:
            logger.debug('Object already in users favorites')
            return Response(
                {'detail': _(already_exist_msg)},
                status=status.HTTP_409_CONFLICT,
            )

        logger.debug('Returning object data')
        serializer = self.get_serializer(obj, many=False, context={'request': request})
        logger.debug(f'Serializer used: {type(serializer)}')

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_from_favorite_action(
        self,
        request: HttpRequest,
        related_model: Model,
        related_model_obj_field: str,
        not_found_msg: str = 'Object not found.',
    ) -> HttpResponse:
        """Remove object from favorites. Returns object data."""
        obj = self.get_object()
        logger.debug(f'Obtained object: {obj}')

        logger.debug('Removing object from users favorites')
        logger.debug(f'Model used: {related_model}')
        deleted, __ = related_model.objects.filter(
            **{related_model_obj_field: obj, 'user': request.user}
        ).delete()

        if not deleted:
            logger.debug('Object not found in users favorites')
            return Response(
                {'detail': _(not_found_msg)},
                status=status.HTTP_404_NOT_FOUND,
            )

        logger.debug('Returning object data')
        serializer = self.get_serializer(obj, many=False, context={'request': request})
        logger.debug(f'Serializer used: {type(serializer)}')

        return Response(serializer.data, status=status.HTTP_200_OK)
