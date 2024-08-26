"""Core exceptions."""

from typing import Any, Type, Callable
from datetime import time

from django.utils.translation import gettext as _
from django.http import HttpRequest, HttpResponse
from django.db.models import Model

from rest_framework.exceptions import APIException
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from .constants import MAX_IMAGE_SIZE_MB


class ExceptionCodes:
    """Class to store common exceptions codes constants."""

    ALREADY_EXIST = 'already_exist'
    SERVICE_UNAVAILABLE = 'service_unavailable'
    AMOUNT_LIMIT_EXCEEDED = 'amount_limit_exceeded'


class ExceptionDetails:
    """Class to store exceptions detail messages."""

    class Images:
        INVALID_IMAGE_FILE = _('Invalid image file passed.')
        INVALID_IMAGE_SIZE = _(f'Image file too large ( > {MAX_IMAGE_SIZE_MB} MB )')

    class Users:
        """Users app exception details."""

        LEARNING_LANGUAGE_ALREADY_EXIST = _('Язык уже добавлен в изучаемые.')
        LANGUAGE_NOT_AVAILABLE = _(
            'The selected language is not yet able for learning.'
        )

    class Vocabulary:
        """Vocabulary app exception details."""

        LANGUAGE_MUST_BE_LEARNING = _('Language must be in your learning languages.')


class AmountLimits:
    """Class to store amount limit constants, detail messages."""

    class Vocabulary:
        MAX_TYPES_AMOUNT = 3
        MAX_TAGS_AMOUNT = 10
        MAX_TRANSLATIONS_AMOUNT = 24
        MAX_NOTES_AMOUNT = 10
        MAX_EXAMPLES_AMOUNT = 10
        MAX_DEFINITIONS_AMOUNT = 10
        MAX_FORMS_AMOUNT = 10
        MAX_IMAGES_AMOUNT = 10
        MAX_QUOTES_AMOUNT = 10
        MAX_SYNONYMS_AMOUNT = 16
        MAX_ANTONYMS_AMOUNT = 16
        MAX_SIMILARS_AMOUNT = 16
        MAX_FORM_GROUPS_AMOUNT = 4

        class Details:
            TYPES_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во типов')
            TAGS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во тегов')
            TRANSLATIONS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во переводов')
            NOTES_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во заметок')
            EXAMPLES_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во примеров')
            DEFINITIONS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во определений')
            FORMS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во форм')
            IMAGES_AMOUNT_EXCEEDED = _(
                'Превышено максимальное кол-во картинок-ассоциаций'
            )
            QUOTES_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во цитат-ассоциаций')
            SYNONYMS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во синонимов')
            ANTONYMS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во антонимов')
            SIMILARS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во похожих слов')
            FORM_GROUPS_AMOUNT_EXCEEDED = _('Превышено максимальное кол-во групп форм')

    class Users:
        MAX_NATIVE_LANGUAGES_AMOUNT = 2
        MAX_LEARNING_LANGUAGES_AMOUNT = 5

        class Details:
            LEARNING_LANGUAGES_AMOUNT_EXCEEDED = _(
                'Превышено максимальное кол-во изучаемых языков'
            )
            NATIVE_LANGUAGES_AMOUNT_EXCEEDED = _(
                'Превышено максимальное кол-во родных языков'
            )

    class Exercises:
        EXERCISE_MAX_WORDS_AMOUNT_LIMIT = 100
        MAX_WORD_SETS_AMOUNT_LIMIT = 50
        MAX_ANSWER_TIME_LIMIT = time(0, 5, 0)
        MIN_ANSWER_TIME_LIMIT = time(0, 0, 30)
        MAX_REPETITIONS_AMOUNT_LIMIT = 10
        MIN_REPETITIONS_AMOUNT_LIMIT = 1

        class Details:
            WORDS_AMOUNT_EXCEEDED = _(
                'Превышено максимальное количество слов для тренировки'
            )
            WORD_SETS_AMOUNT_EXCEEDED = _(
                'Превышено максимальное количество наборов слов'
            )
            MAX_ANSWER_TIME_EXCEEDED = _(
                'Превышено максимальное ограничение времени ответа'
            )
            MIN_ANSWER_TIME_EXCEEDED = _(
                'Превышено минимальное ограничение времени ответа'
            )
            MAX_REPETITIONS_LIMIT_EXCEEDED = _(
                'Превышено максимальное ограничение количества повторов'
            )
            MIN_REPETITIONS_LIMIT_EXCEEDED = _(
                'Превышено минимальное ограничение количества повторов'
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
