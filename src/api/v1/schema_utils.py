from rest_framework.serializers import (
    CharField,
    ListField,
)
from drf_spectacular.utils import (
    OpenApiResponse,
    OpenApiExample,
    inline_serializer,
)

unauthorized_response = OpenApiResponse(
    description=(
        'Пользователь не авторизован.\n' 'Не был передан заголовок Authorization.',
    ),
    response=inline_serializer(
        name='unauthorized',
        fields={
            'detail': CharField(),
        },
    ),
    examples=[
        OpenApiExample(
            name='unauthorized',
            value={
                'detail': 'Учетные данные не были предоставлены.',
            },
        ),
    ],
)

not_found_response = OpenApiResponse(
    description=('Страница по этому url не найдена.',),
    response=inline_serializer(
        name='not_found',
        fields={
            'detail': CharField(),
        },
    ),
    examples=[
        OpenApiExample(
            name='not_found',
            value={
                'detail': 'Страница не найдена.',
            },
        ),
    ],
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
