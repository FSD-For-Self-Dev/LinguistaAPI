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

    class Images:
        IMAGE_FILE_OR_URL_IS_REQUIRED = 'empty_image'

    class Languages:
        LANGUAGE_INVALID = 'invalid_language'

    class Vocabulary:
        WORDS_MUST_BE_SAME_LANGUAGE = 'words_same_language'
        EXAMPLE_MUST_BE_SAME_LANGUAGE = 'examples_same_language'
        DEFINITION_MUST_BE_SAME_LANGUAGE = 'definitions_same_language'
        FORM_GROUP_MUST_BE_SAME_LANGUAGE = 'form_groups_same_language'
        SYNONYM_MUST_BE_SAME_LANGUAGE = 'synonyms_same_language'
        ANTONYM_MUST_BE_SAME_LANGUAGE = 'antonyms_same_language'
        FORM_MUST_BE_SAME_LANGUAGE = 'forms_same_language'
        SIMILAR_MUST_BE_SAME_LANGUAGE = 'similars_same_language'

        WORDS_MUST_DIFFER = 'words_must_differ'
        SYNONYMS_MUST_DIFFER = 'synonyms_must_differ'
        ANTONYMS_MUST_DIFFER = 'antonyms_must_differ'
        FORMS_MUST_DIFFER = 'forms_must_differ'
        SIMILARS_MUST_DIFFER = 'similars_must_differ'


class ExceptionDetails:
    """Class to store exceptions detail messages."""

    class Images:
        INVALID_IMAGE_FILE = _('Invalid image file passed.')
        INVALID_IMAGE_SIZE = _(f'Image file too large ( > {MAX_IMAGE_SIZE_MB} MB ).')
        IMAGE_FILE_OR_URL_IS_REQUIRED = _('No image file or url passed.')

    class Languages:
        """Languages app exception details."""

        LEARNING_LANGUAGE_ALREADY_EXIST = _(
            'This language has been already added to your learning languages.'
        )
        LANGUAGE_NOT_AVAILABLE = _(
            'The selected language is not yet able for learning.'
        )
        LANGUAGE_MUST_BE_LEARNING = _('Language must be in your learning languages.')
        LANGUAGE_MUST_BE_LEARNING_OR_NATIVE = _(
            'Language must be in your learning or native languages.'
        )
        LANGUAGE_MUST_BE_NATIVE = _('Language must be in your native languages.')

    class Exercises:
        """Exercises app exception details."""

        WORD_SET_ALREADY_EXIST = _('This word set already exists.')

    class Vocabulary:
        """Vocabulary app exception details."""

        FORM_GROUP_ALREADY_EXIST = _('Form group with this name already exists.')

        WORDS_MUST_BE_SAME_LANGUAGE = _('Words must be in the same language.')
        EXAMPLE_MUST_BE_SAME_LANGUAGE = _(
            'The usage examples should be in the same language as the word itself.'
        )
        DEFINITION_MUST_BE_SAME_LANGUAGE = _(
            'The definitions should be in the same language as the word itself.'
        )
        FORM_GROUP_MUST_BE_SAME_LANGUAGE = _(
            'The form groups should be in the same language as the word itself.'
        )
        SYNONYM_MUST_BE_SAME_LANGUAGE = _(
            'The synonyms should be in the same language as the word itself.'
        )
        ANTONYM_MUST_BE_SAME_LANGUAGE = _(
            'The antonyms should be in the same language as the word itself.'
        )
        FORM_MUST_BE_SAME_LANGUAGE = _(
            'The forms should be in the same language as the word itself.'
        )
        SIMILAR_MUST_BE_SAME_LANGUAGE = _(
            'The similar words should be in the same language as the word itself.'
        )

        WORDS_MUST_BE_SAME_LANGUAGE_AS_DEFINITION = _(
            'The words should be in the same language as the definition itself.'
        )
        WORDS_MUST_BE_SAME_LANGUAGE_AS_EXAMPLE = _(
            'The words should be in the same language as the usage example itself.'
        )

        WORDS_MUST_DIFFER = _('Words must be different.')
        SYNONYMS_MUST_DIFFER = _('The word itself cannot be its own synonym.')
        ANTONYMS_MUST_DIFFER = _('The word itself cannot be its own antonym.')
        FORMS_MUST_DIFFER = _('The word itself cannot be its own form.')
        SIMILARS_MUST_DIFFER = _('The word itself cannot be its own similar.')

        WORD_ALREADY_EXIST = _(
            'This word already exists in your vocabulary. Update it?'
        )
        EXAMPLE_ALREADY_EXIST = _(
            'This usage example already exists in your vocabulary. Update it?'
        )
        DEFINITION_ALREADY_EXIST = _(
            'This definition already exists in your vocabulary. Update it?'
        )
        TRANSLATION_ALREADY_EXIST = _(
            'This translation already exists in your vocabulary. Update it?'
        )
        TAG_ALREADY_EXIST = _('This tag already exists in your vocabulary. Update it?')
        FORM_GROUP_ALREADY_EXIST = _(
            'This form group already exists in your vocabulary. Update it?'
        )
        COLLECTION_ALREADY_EXIST = _(
            'This collection already exists in your vocabulary. Update it?'
        )
        NOTE_ALREADY_EXIST = _('This note already exists for this word.')


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
            TYPES_AMOUNT_EXCEEDED = _('Word types amount limit exceeded.')
            TAGS_AMOUNT_EXCEEDED = _('Word tags amount limit exceeded.')
            TRANSLATIONS_AMOUNT_EXCEEDED = _('Word translations amount limit exceeded.')
            NOTES_AMOUNT_EXCEEDED = _('Word notes amount limit exceeded.')
            EXAMPLES_AMOUNT_EXCEEDED = _('Word examples amount limit exceeded.')
            DEFINITIONS_AMOUNT_EXCEEDED = _('Word definitions amount limit exceeded.')
            FORMS_AMOUNT_EXCEEDED = _('Word forms amount limit exceeded.')
            IMAGES_AMOUNT_EXCEEDED = _('Word image-associations amount limit exceeded.')
            QUOTES_AMOUNT_EXCEEDED = _('Word quote-associations amount limit exceeded.')
            SYNONYMS_AMOUNT_EXCEEDED = _('Word synonyms amount limit exceeded.')
            ANTONYMS_AMOUNT_EXCEEDED = _('Word antonyms amount limit exceeded.')
            SIMILARS_AMOUNT_EXCEEDED = _('Similar words amount limit exceeded.')
            FORM_GROUPS_AMOUNT_EXCEEDED = _('Word form groups amount limit exceeded.')

    class Languages:
        MAX_NATIVE_LANGUAGES_AMOUNT = 2
        MAX_LEARNING_LANGUAGES_AMOUNT = 5

        class Details:
            LEARNING_LANGUAGES_AMOUNT_EXCEEDED = _(
                'Learning languages amount limit exceeded.'
            )
            NATIVE_LANGUAGES_AMOUNT_EXCEEDED = _(
                'Native languages amount limit exceeded.'
            )

    class Exercises:
        EXERCISE_MAX_WORDS_AMOUNT_LIMIT = 100
        MAX_WORD_SETS_AMOUNT_LIMIT = 50
        MAX_ANSWER_TIME_LIMIT = time(0, 5, 0)
        MIN_ANSWER_TIME_LIMIT = time(0, 0, 30)
        MAX_REPETITIONS_AMOUNT_LIMIT = 10
        MIN_REPETITIONS_AMOUNT_LIMIT = 1

        class Details:
            WORDS_AMOUNT_EXCEEDED = _('Words amount limit exceeded for this exercise.')
            WORD_SETS_AMOUNT_EXCEEDED = _(
                'Word sets amount limit exceeded for this exercise.'
            )
            MAX_ANSWER_TIME_EXCEEDED = _('Maximum time limit exceeded.')
            MIN_ANSWER_TIME_EXCEEDED = _('Minimum time limit exceeded.')
            MAX_REPETITIONS_LIMIT_EXCEEDED = _(
                'Maximum repetitions amount limit exceeded.'
            )
            MIN_REPETITIONS_LIMIT_EXCEEDED = _(
                'Minimum repetitions amount limit exceeded.'
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
