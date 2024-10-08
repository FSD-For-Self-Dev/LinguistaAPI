"""Utils to use in API schema."""

from rest_framework.serializers import (
    CharField,
    ListField,
)
from drf_spectacular.utils import (
    OpenApiResponse,
    OpenApiExample,
    inline_serializer,
)


def get_detail_response(detail_message: str, description: str = '') -> OpenApiResponse:
    return OpenApiResponse(
        description=description,
        response=inline_serializer(
            name='detail_message_serializer',
            fields={
                'detail': CharField(),
            },
        ),
        examples=[
            OpenApiExample(
                name='detail_message',
                value={
                    'detail': detail_message,
                },
            ),
        ],
    )


def get_validation_error_response(examples: list[OpenApiExample]) -> OpenApiResponse:
    return OpenApiResponse(
        description='Ошибки валидации',
        response=inline_serializer(
            name='exception_details_serializer',
            fields={
                'non_field_errors': ListField(),
            },
        ),
        examples=examples,
    )


def get_conflict_response(examples: list[OpenApiExample]) -> OpenApiResponse:
    return OpenApiResponse(
        response=inline_serializer(
            name='conflict_detail',
            fields={
                'exception_code': CharField(),
                'detail': CharField(),
            },
        ),
        examples=examples,
    )
