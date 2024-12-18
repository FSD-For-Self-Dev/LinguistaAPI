"""Core exceptions."""

from typing import Type, Callable

from django.utils.translation import gettext as _
from django.http import HttpRequest, HttpResponse
from django.db.models import Model

from rest_framework.exceptions import APIException
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from apps.core.constants import ExceptionCodes


class AmountLimitExceeded(APIException):
    """Custom exception to raise when some objects amount limit is exceeded."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = _('Amount limit exceeded.')
    default_code = ExceptionCodes.AMOUNT_LIMIT_EXCEEDED

    def __init__(
        self,
        amount_limit: int,
        detail: str | None = None,
        code: str | None = None,
    ) -> None:
        self.amount_limit = amount_limit
        super().__init__(detail, code)

    def get_detail_response(self, request: HttpRequest) -> HttpResponse:
        return Response(
            {
                'exception_code': self.default_code,
                'detail': self.detail,
                'amount_limit': self.amount_limit,
            },
            status=self.status_code,
        )


class ObjectAlreadyExist(APIException):
    """
    Custom exception to raise when object that need to be created already exists.
    """

    status_code = status.HTTP_409_CONFLICT
    default_detail = _('This object already exists.')
    default_code = ExceptionCodes.ALREADY_EXIST

    def __init__(
        self,
        detail: str | None = None,
        code: str | None = None,
        existing_object: Type[Model] | None = None,
        new_object_data: dict | None = None,
        serializer_class: Serializer | None = None,
        conflict_object_index: int | None = None,
        conflict_field: str | None = None,
    ) -> None:
        self.code = code or self.default_code
        self.existing_object = existing_object
        self.new_object_data = new_object_data
        self.serializer_class = serializer_class
        self.conflict_object_index = conflict_object_index
        self.conflict_field = conflict_field
        super().__init__(detail, code)

    def get_detail_response(
        self,
        request: HttpRequest,
        existing_obj_representation: Callable | None = None,
    ) -> HttpResponse:
        """
        Add existing object details to response if its serializer class is passed.
        """
        try:
            if existing_obj_representation:
                response_data = {
                    'exception_code': self.code,
                    'detail': self.detail,
                    'existing_object': existing_obj_representation(
                        self.existing_object
                    ),
                }

            elif self.serializer_class:
                response_data = {
                    'exception_code': self.code,
                    'detail': self.detail,
                    'existing_object': self.serializer_class(
                        self.existing_object, context={'request': request}
                    ).data,
                    'new_object': self.new_object_data,
                }

            else:
                response_data = {
                    'exception_code': self.code,
                    'detail': self.detail,
                }

            if self.conflict_object_index is not None:
                response_data['conflict_object_index'] = self.conflict_object_index

            if self.conflict_field is not None:
                response_data['conflict_field'] = self.conflict_field

            return Response(response_data, status=self.status_code)

        except Exception:
            return Response(
                {
                    'exception_code': self.code,
                    'detail': self.detail,
                },
                status=self.status_code,
            )


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = ExceptionCodes.SERVICE_UNAVAILABLE
