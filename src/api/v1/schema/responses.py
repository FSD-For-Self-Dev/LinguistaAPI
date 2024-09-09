"""API schema core responses."""

from rest_framework.serializers import (
    CharField,
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

user_patch_validation_error_examples = [
    OpenApiExample(
        name='username_is_taken',
        description='Переданный юзернейм занят другим пользователем.',
        value={'username': ['Пользователь с таким именем уже существует.']},
    ),
    OpenApiExample(
        name='native_languages_amount_limit',
        description='Количество родных языков превышает заданные ограничения.',
        value={'native_languages': ['Native languages amount limit exceeded.']},
    ),
    OpenApiExample(
        name='invalid_language',
        description='Передан некорректный язык.',
        value={'native_languages': ['Объект с name=Englishы не существует.']},
    ),
    OpenApiExample(
        name='invalid_image',
        description='Передан некорректный файл.',
        value={'image': ['Загруженный файл не является корректным файлом.']},
    ),
    OpenApiExample(
        name='invalid_first_name',
        description='Имя содержит неразрешенные символы.',
        value={
            'first_name': [
                'Acceptable characters: Letters from any language, Apostrophe, Space. Make sure name begin with a letter.'
            ]
        },
    ),
]
