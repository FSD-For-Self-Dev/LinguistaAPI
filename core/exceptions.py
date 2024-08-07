"""Core exceptions."""

from typing import Any, Type

from django.utils.translation import gettext as _
from django.http import HttpRequest, HttpResponse
from django.db.models import Model

from rest_framework.exceptions import APIException
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import Serializer


class AmountLimitExceeded(APIException):
    """Custom exception to raise when some objects amount limit is exceeded."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Amount limit exceeded.')
    default_code = 'amount_limit_exceeded'

    def get_detail_response(self, request: HttpRequest) -> HttpResponse:
        return Response(
            {
                'detail': self.detail,
            },
            status=self.status_code,
        )


class ObjectAlreadyExist(APIException):
    """
    Custom exception to raise when object that need to be created already exists.
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = _('This object already exists.')
    default_code = 'object_already_exist'

    def __init__(
        self,
        detail: str | None = None,
        code: str | None = None,
        existing_object: Type[Model] | None = None,
        serializer_class: Serializer | None = None,
        passed_data: dict[str, Any] | None = None,
    ) -> None:
        self.existing_object = existing_object
        self.serializer_class = serializer_class
        self.passed_data = passed_data
        super().__init__(detail, code)

    def get_detail_response(self, request: HttpRequest) -> HttpResponse:
        """
        Add existing object details to response if its serializer class is passed.
        """
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
            status=self.status_code,
        )


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = 'service_unavailable'
