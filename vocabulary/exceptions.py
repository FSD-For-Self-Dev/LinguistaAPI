"""Исключения приложения vocabulary."""

from rest_framework.exceptions import APIException
from rest_framework import status


class AmountLimitExceeded(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Превышен лимит кол-ва.'
    default_code = 'amount_limit_exceeded'


class ObjectAlreadyExist(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Объект уже есть в вашем словаре.'
    default_code = 'object_already_exist'

    def __init__(
        self, detail=None, code=None, existing_object=None, serializer_class=None
    ):
        self.object = existing_object
        self.serializer_class = serializer_class
        super().__init__(detail, code)


class ObjectDoesNotExistWithDetail(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Объект не найден.'
    default_code = 'object_not_exist'
