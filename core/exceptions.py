"""Core exceptions."""

from django.utils.translation import gettext as _

from rest_framework.exceptions import APIException
from rest_framework import status
from rest_framework.response import Response


class AmountLimitExceeded(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Amount limit exceeded.')
    default_code = 'amount_limit_exceeded'


class ObjectAlreadyExist(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _('This object already exists.')
    default_code = 'object_already_exist'

    def __init__(
        self,
        detail=None,
        code=None,
        existing_object=None,
        serializer_class=None,
        passed_data=None,
    ):
        self.existing_object = existing_object
        self.serializer_class = serializer_class
        self.passed_data = passed_data
        super().__init__(detail, code)

    def get_detail_response(self, request):
        if self.serializer_class:
            return Response(
                {
                    'detail': self.detail,
                    'existing_object': self.serializer_class(
                        self.existing_object, context={'request': request}
                    ).data,
                },
                status=self.status_code,
            )
        return Response(
            {
                'detail': self.detail,
            },
            status=status.HTTP_409_CONFLICT,
        )


class ObjectDoesNotExistWithDetail(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _('Object not found.')
    default_code = 'object_not_exist'
