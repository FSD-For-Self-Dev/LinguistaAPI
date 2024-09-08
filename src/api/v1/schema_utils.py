from rest_framework.serializers import (
    CharField,
    ListField,
)
from drf_spectacular.utils import (
    OpenApiResponse,
    OpenApiExample,
    inline_serializer,
)


def get_detail_response(detail_message, description=''):
    return OpenApiResponse(
        description=description,
        response=inline_serializer(
            name='detail_inline',
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


def get_validation_error_response(examples):
    return OpenApiResponse(
        description='Ошибки валидации',
        response=inline_serializer(
            name='exception_details',
            fields={
                'non_field_errors': ListField(),
            },
        ),
        examples=examples,
    )
