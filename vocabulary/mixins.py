from django.db import transaction, IntegrityError
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

from .exceptions import AmountLimitExceeded


class AlreadyExistHandlerMixin:
    pass


class ActionsWithRelatedObjectsMixin(AlreadyExistHandlerMixin):
    @transaction.atomic
    def add_from_vocabulary(
        self, request, instance, serializer_class, objs_related_name, *args, **kwargs
    ):
        serializer = serializer_class(
            data=request.data, context={'request': request, 'view': self}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        _objs = instance.__getattribute__(objs_related_name).all()
        self.check_amount_limit(
            _objs_amount=_objs.count(),
            amount_limit=kwargs.get('amount_limit', ''),
            amountlimit_detail=kwargs.get(
                'amountlimit_detail', 'Amount limit exceeded.'
            ),
        )
        return self.get_list_response(
            request,
            instance,
            objs_related_name=objs_related_name,
            response_objs_related_name=kwargs.get(
                'response_objs_related_name', objs_related_name
            ),
            objs=_objs,
        )

    @transaction.atomic
    def _list_and_create_action(
        self,
        request,
        objs_related_name,
        *args,
        **kwargs,
    ):
        """Осуществить методы list, create для связанных объектов."""
        instance = self.get_object()
        _objs = instance.__getattribute__(objs_related_name).all()
        match request.method:
            case 'GET':
                return self.get_list_response(
                    request,
                    instance,
                    objs_related_name=objs_related_name,
                    response_objs_related_name=kwargs.get(
                        'response_objs_related_name', objs_related_name
                    ),
                    objs=_objs,
                    serializer_class=kwargs.get(
                        'list_serializer_class', self.get_serializer_class()
                    ),
                )
            case 'POST':
                from_vocabulary_param = kwargs.get('from_vocabulary', None)
                if from_vocabulary_param in ('True', 'true', 't', '1', 'y', 'yes'):
                    assert 'from_vocabulary_serializer' in kwargs, (
                        '`from_vocabulary_serializer` must be passed in kwargs, when '
                        '`from_vocabulary` query param is available.'
                    )
                    serializer_class = kwargs.get('from_vocabulary_serializer')
                    return self.add_from_vocabulary(
                        request,
                        instance=instance,
                        serializer_class=serializer_class,
                        objs_related_name=objs_related_name,
                        response_objs_related_name=kwargs.get(
                            'response_objs_related_name', objs_related_name
                        ),
                        amount_limit=kwargs.get('amount_limit', ''),
                        amountlimit_detail=kwargs.get(
                            'amountlimit_detail', 'Amount limit exceeded.'
                        ),
                    )

                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                try:
                    self.check_amount_limit(
                        _objs_amount=_objs.count(),
                        amount_limit=kwargs.get('amount_limit', ''),
                        amountlimit_detail=kwargs.get(
                            'amountlimit_detail', 'Amount limit exceeded.'
                        ),
                    )
                    _new_obj = serializer.save()
                except IntegrityError:
                    handler_data = self.integrity_handler(
                        serializer,
                        detail_message=kwargs.get(
                            'conflict_detail', 'This object already exist.'
                        ),
                        update_param=request.query_params.get('update', None),
                    )
                    conflicts = handler_data.get('conflicts')
                    if conflicts:
                        return Response(conflicts, status=status.HTTP_409_CONFLICT)
                    _new_obj = handler_data.get('obj')

                add_intermediate = kwargs.get('add_intermediate', False)
                if add_intermediate:
                    instance.__getattribute__(objs_related_name).add(
                        _new_obj, through_defaults=kwargs.get('through_defaults', None)
                    )

                return self.get_list_response(
                    request,
                    instance,
                    objs_related_name=objs_related_name,
                    response_objs_related_name=kwargs.get(
                        'response_objs_related_name', objs_related_name
                    ),
                )

    @transaction.atomic
    def _detail_action(
        self,
        request,
        objs_related_name,
        lookup_attr,
        lookup_field='pk',
        *args,
        **kwargs,
    ):
        """Осуществить методы retrieve, partial_update, destroy для связанных объектов."""
        instance = self.get_object()
        try:
            _obj = instance.__getattribute__(objs_related_name).get(
                **{lookup_field: kwargs.get(lookup_attr)}
            )
        except ObjectDoesNotExist:
            raise NotFound(detail=kwargs.get('notfounderror_msg', 'Not found.'))

        match request.method:
            case 'GET':
                return Response(self.get_serializer(_obj).data)
            case 'PATCH':
                serializer = self.get_serializer(
                    instance=_obj, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                try:
                    serializer.save()
                except IntegrityError:  # use Integrity handler
                    return Response(
                        {
                            'detail': kwargs.get(
                                'alreadyexist_detail', 'This object already exist.'
                            )
                        },
                        status=status.HTTP_409_CONFLICT,
                    )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            case 'DELETE':
                instance.__getattribute__(objs_related_name).remove(_obj)
                return self.get_list_response(
                    request,
                    instance,
                    objs_related_name=kwargs.get(
                        'list_objs_related_name', objs_related_name
                    ),
                    response_objs_related_name=kwargs.get(
                        'response_objs_related_name', objs_related_name
                    ),
                    serializer_class=kwargs.get(
                        'list_serializer_class', self.get_serializer_class()
                    ),
                )

    def get_list_response(
        self,
        request,
        instance,
        objs_related_name,
        response_objs_related_name,
        *args,
        **kwargs,
    ):
        _objs = kwargs.get('objs', instance.__getattribute__(objs_related_name).all())
        serializer_class = kwargs.get('serializer_class', self.get_serializer_class())
        serializer = serializer_class(_objs, many=True, context={'request': request})
        return Response(
            {'count': _objs.count(), response_objs_related_name: serializer.data},
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def check_amount_limit(_objs_amount, amount_limit, amountlimit_detail):
        if amount_limit and _objs_amount >= amount_limit:
            raise AmountLimitExceeded(detail=amountlimit_detail)


class FavoriteMixin:
    pass
