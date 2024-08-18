"""Core exceptions."""

from typing import Any, Type, Callable

from django.utils.translation import gettext as _
from django.http import HttpRequest, HttpResponse
from django.db.models import Model

from rest_framework.exceptions import APIException
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import Serializer


class ExceptionCodes:
    """Class to store common exceptions codes constants."""

    ALREADY_EXIST = 'already_exist'
    SERVICE_UNAVAILABLE = 'service_unavailable'
    AMOUNT_LIMIT_EXCEEDED = 'amount_limit_exceeded'


class ExceptionDetails:
    """Class to store exceptions detail messages."""

    class Users:
        """Users app exception details."""

        LEARNING_LANGUAGE_ALREADY_EXIST = _('Язык уже добавлен в изучаемые.')
        LANGUAGE_NOT_AVAILABLE = _(
            'The selected language is not yet able for learning.'
        )


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
        serializer_class: Serializer | None = None,
        passed_data: dict[str, Any] | None = None,
    ) -> None:
        self.existing_object = existing_object
        self.serializer_class = serializer_class
        self.passed_data = passed_data
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
                return Response(
                    {
                        'exception_code': self.default_code,
                        'detail': self.detail,
                        'existing_object': existing_obj_representation(
                            self.existing_object
                        ),
                    },
                    status=self.status_code,
                )
            if self.serializer_class:
                return Response(
                    {
                        'exception_code': self.default_code,
                        'detail': self.detail,
                        'existing_object': self.serializer_class(
                            self.existing_object, context={'request': request}
                        ).data,
                    },
                    status=self.status_code,
                )
            else:
                return Response(
                    {
                        'exception_code': self.default_code,
                        'detail': self.detail,
                    },
                    status=self.status_code,
                )

        except Exception:
            return Response(
                {
                    'exception_code': self.default_code,
                    'detail': self.detail,
                },
                status=self.status_code,
            )


class ServiceUnavailable(APIException):
    status_code = 503
    default_detail = 'Service temporarily unavailable, try again later.'
    default_code = ExceptionCodes.SERVICE_UNAVAILABLE
