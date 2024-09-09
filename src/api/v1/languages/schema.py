"""Languages schema data."""

from rest_framework import status
from rest_framework.serializers import (
    CharField,
    IntegerField,
    ListField,
)
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
    OpenApiExample,
    inline_serializer,
    PolymorphicProxySerializer,
)

from apps.core.exceptions import ExceptionCodes, ExceptionDetails, AmountLimits

from api.v1.vocabulary.serializers import (
    LearningLanguageWithLastWordsSerailizer,
)
from api.v1.languages.serializers import (
    LanguageSerializer,
    LearningLanguageSerailizer,
    NativeLanguageSerailizer,
    LanguageCoverImageSerailizer,
)

from ..schema.responses import (
    unauthorized_response,
)


data = {
    'LanguageViewSet': {
        'tags': ['learning_languages'],
        'learning_languages_list': {
            'summary': 'Просмотр списка изучаемых языков пользователя',
            'description': (
                'Возвращает список всех изучаемых языков пользователя. '
                'Требуется авторизация.'
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: PolymorphicProxySerializer(
                    'many_false_list',
                    serializers=[
                        inline_serializer(
                            name='learning_languages_list',
                            fields={
                                'count': IntegerField(),
                                'results': LearningLanguageWithLastWordsSerailizer(
                                    many=True
                                ),
                            },
                        ),
                    ],
                    many=False,
                    resource_type_field_name=None,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
            'parameters': [
                OpenApiParameter(
                    'ordering',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Принимает поле, по которому необходимо сортировать результаты. '
                        'Доступные поля: '
                        'words_count (количество слов языка), created (дата добавления). '
                        'Для сортировки по убыванию используется префикс `-`. '
                        'Пример использования: `api/languages/?ordering=-words_count`.'
                    ),
                ),
                OpenApiParameter(
                    'search',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Поиск по названию, локальному названию языков. '
                        'Пример использования: `api/languages/?search=English`.'
                    ),
                ),
            ],
        },
        'learning_language_create': {
            'summary': 'Добавление изучаемых языков',
            'description': (
                'Добавляет переданные языки в изучаемые для пользователя. '
                'Требуется авторизация.'
            ),
            'parameters': [
                OpenApiParameter(
                    'no_words',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Если передан этот параметр, в ответе не будут отображаться '
                        'последние добавленные слова для каждого языка. '
                        'Используется для оптимизации времени ответа сервера. '
                        'Пример использования: `api/languages/?no_words`.'
                    ),
                ),
            ],
            'request': LearningLanguageSerailizer(many=True),
            'responses': {
                status.HTTP_201_CREATED: OpenApiResponse(
                    description=(
                        'Языки успешно добавлены в изучаемые. '
                        'Возвращается обновленный список всех изучаемых языков.'
                    ),
                    response=inline_serializer(
                        name='learning_languages_list_after_create',
                        fields={
                            'count': IntegerField(),
                            'results': LearningLanguageWithLastWordsSerailizer(
                                many=True
                            ),
                        },
                    ),
                ),
                status.HTTP_409_CONFLICT: OpenApiResponse(
                    description=(
                        'Возможные конфликты:\n'
                        '\tОдин или несколько языков уже являются изучаемыми.'
                        '\tПревышено ограничение на количество изучаемых языков.'
                    ),
                    response=inline_serializer(
                        name='conflicts_detail_serializer',
                        fields={
                            'exception_code': CharField(),
                            'detail': CharField(),
                        },
                    ),
                    examples=[
                        OpenApiExample(
                            name=ExceptionCodes.ALREADY_EXIST,
                            value={
                                'exception_code': ExceptionCodes.ALREADY_EXIST,
                                'detail': ExceptionDetails.Languages.LEARNING_LANGUAGE_ALREADY_EXIST,
                                'existing_object': 'English',
                            },
                        ),
                        OpenApiExample(
                            name=ExceptionCodes.AMOUNT_LIMIT_EXCEEDED,
                            value={
                                'exception_code': ExceptionCodes.AMOUNT_LIMIT_EXCEEDED,
                                'detail': AmountLimits.Languages.Details.LEARNING_LANGUAGES_AMOUNT_EXCEEDED,
                                'amount_limit': AmountLimits.Languages.MAX_LEARNING_LANGUAGES_AMOUNT,
                            },
                        ),
                    ],
                ),
                status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                    description=(
                        'Ошибки валидации:\n'
                        '\tОдин или несколько языков недоступны для изучения на данный момент.'
                        '\tОдин или несколько языков не найдены по переданному названию.'
                    ),
                    response=inline_serializer(
                        name='language_validation_details',
                        fields={
                            'language': ListField(),
                        },
                    ),
                    examples=[
                        OpenApiExample(
                            name='language_not_available',
                            value=[
                                {},
                                {
                                    'language': [
                                        ExceptionDetails.Languages.LANGUAGE_NOT_AVAILABLE
                                    ]
                                },
                            ],
                        ),
                        OpenApiExample(
                            name='language_not_found',
                            value=[
                                {},
                                {'language': ['Объект с name=Jaanese не существует.']},
                            ],
                        ),
                    ],
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'learning_language_retrieve': {
            'summary': 'Просмотр профиля изучаемого языка',
            'description': (
                'Возвращает изучаемый язык и список слов этого языка '
                'из словаря пользователя. \n'
                'Требуется авторизация.'
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: OpenApiResponse(
                    description=(
                        'Возвращается информация изучаемого языка и список слов '
                        '`words` с пагинацией.'
                    ),
                    response=LearningLanguageSerailizer,
                    examples=[
                        OpenApiExample(
                            name='one word',
                            value={
                                'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                                'slug': 'e6EyeJGM7ggQyxhj54SMb6J8Ni3B4IZZo8',
                                'language': {
                                    'id': 'string',
                                    'name': 'string',
                                    'name_local': 'string',
                                    'flag_icon': 'string',
                                },
                                'level': 'string',
                                'cover': 'string',
                                'cover_height': 0,
                                'cover_width': 0,
                                'words_count': 0,
                                'inactive_words_count': 0,
                                'active_words_count': 0,
                                'mastered_words_count': 0,
                                'words': {
                                    'count': 0,
                                    'next': 'http://api.example.org/accounts/?page=4',
                                    'previous': 'http://api.example.org/accounts/?page=2',
                                    'results': [
                                        {
                                            'id': 51028152463805901552645234066848599722,
                                            'slug': 'e6EyeJGM7ggQyxhj54SMb6J8Ni3B4IZZo9',
                                            'language': 'English',
                                            'text': 'string',
                                            'author': 'string',
                                            'created': '2024-08-17 14:04',
                                            'modified': '2024-08-17 14:04',
                                            'types': ['Adjective', 'Verb', 'Noun'],
                                            'tags': [],
                                            'form_groups': [],
                                            'favorite': False,
                                            'is_problematic': False,
                                            'activity_status': 'Неактивное',
                                            'last_exercise_date': None,
                                            'translations_count': 0,
                                            'translations': [],
                                            'images_count': 0,
                                            'image': 'string',
                                        },
                                    ],
                                },
                            },
                        ),
                    ],
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'learning_language_destroy': {
            'summary': 'Удаление языка из изучаемых',
            'description': (
                'Удаляет выбранный язык из изучаемых. \n' 'Требуется авторизация.'
            ),
            'parameters': [
                OpenApiParameter(
                    'delete_words',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Если передан этот параметр, слова этого языка будут также '
                        'удалены из словаря пользователя. '
                        'Пример использования: '
                        '`api/languages/<learning_language_slug>/?delete_words`.'
                    ),
                ),
            ],
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: OpenApiResponse(
                    description=(
                        'Язык удален из изучаемых, слова этого языка остались в '
                        'словаре пользователя.'
                    ),
                    response=None,
                ),
                status.HTTP_200_OK: OpenApiResponse(
                    description=(
                        'Язык удален из изучаемых, возвращено кол-во удаленных слов, '
                        'если был передан параметр `delete_words`.'
                    ),
                    response=inline_serializer(
                        name='deleted_words_info',
                        fields={'deleted_words': IntegerField()},
                    ),
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'language_collections_list': {
            'summary': 'Просмотр списка коллекций изучаемого языка',
            'description': (
                'Возвращает изучаемый язык и коллекции пользователя, в которых есть'
                ' слова выбранного изучаемого языка. \n'
                'Требуется авторизация.'
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: OpenApiResponse(
                    description=(
                        'Возвращается информация изучаемого языка и список коллекций '
                        '`collections` с пагинацией.'
                    ),
                    response=LearningLanguageSerailizer,
                    examples=[
                        OpenApiExample(
                            name='one collection',
                            value={
                                'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                                'slug': 'e6EyeJGM7ggQyxhj54SMb6J8Ni3B4IZZo8',
                                'language': {
                                    'id': 'string',
                                    'name': 'string',
                                    'name_local': 'string',
                                    'flag_icon': 'string',
                                },
                                'level': 'string',
                                'cover': 'string',
                                'cover_height': 0,
                                'cover_width': 0,
                                'words_count': 0,
                                'inactive_words_count': 0,
                                'active_words_count': 0,
                                'mastered_words_count': 0,
                                'collections': {
                                    'count': 0,
                                    'next': 'http://api.example.org/accounts/?page=4',
                                    'previous': 'http://api.example.org/accounts/?page=2',
                                    'results': [
                                        {
                                            'id': 51028152463805901552645234066848599722,
                                            'slug': 'e6EyeJGM7ggQyxhj54SMb6J8Ni3B4IZZo9',
                                            'author': 'string',
                                            'title': 'string',
                                            'description': 'string',
                                            'favorite': False,
                                            'words_count': 0,
                                            'last_3_words': ['string'],
                                            'created': '2024-07-07 11:06',
                                            'modified': '2024-07-07 11:06',
                                        },
                                    ],
                                },
                            },
                        ),
                    ],
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'native_languages_list': {
            'summary': 'Просмотр списка родных языков пользователя',
            'description': (
                'Возвращает список родных языков пользователя, '
                'сортированных по дате добавления, названию. '
                'Требуется авторизация.'
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: NativeLanguageSerailizer(many=True),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
            'parameters': [
                OpenApiParameter(
                    'ordering',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Принимает поле, по которому необходимо сортировать результаты. '
                        'Доступные поля: - .'
                    ),
                ),
            ],
        },
        'all_languages_list': {
            'summary': 'Просмотр списка изучаемых и родных языков пользователя',
            'description': (
                'Возвращает список изучаемых и родных языков пользователя, '
                'сортированных по популярности, названию. '
                'Требуется авторизация.'
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageSerializer(many=True),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
            'parameters': [
                OpenApiParameter(
                    'search',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Поиск по названию, локальному названию языков. '
                        'Пример использования: `api/languages/all/?search=English`.'
                    ),
                ),
            ],
        },
        'all_languages_global_list': {
            'summary': 'Просмотр списка всех языков',
            'description': (
                'Возвращает список всех языков мира с сортировкой по '
                'популярности изучения, названию.'
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageSerializer(many=True),
            },
            'parameters': [
                OpenApiParameter(
                    'ordering',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Принимает поле, по которому необходимо сортировать результаты. '
                        'Доступные поля: - .'
                    ),
                ),
                OpenApiParameter(
                    'search',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Поиск по названию, локальному названию языков. '
                        'Пример использования: `api/languages/?search=English`.'
                    ),
                ),
            ],
        },
        'languages_available_for_learning_list': {
            'summary': 'Просмотр списка языков доступных для изучения',
            'description': (
                'Возвращает список языков, доступных для изучения на платформе, '
                'которые пользователь еще не добавил в изучаемые языки. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageSerializer(many=True),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
            'parameters': [
                OpenApiParameter(
                    'ordering',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Принимает поле, по которому необходимо сортировать результаты. '
                        'Доступные поля: - .'
                    ),
                ),
                OpenApiParameter(
                    'search',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Поиск по названию, локальному названию языков. '
                        'Пример использования: `api/languages/?search=English`.'
                    ),
                ),
            ],
        },
        'interface_switch_languages_list': {
            'summary': 'Просмотр списка языков доступных для перевода интерфейса',
            'description': (
                'Возвращает список языков, на которые доступен перевод интерфейса '
                'платформы.'
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageSerializer(many=True),
            },
            'parameters': [
                OpenApiParameter(
                    'ordering',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Принимает поле, по которому необходимо сортировать результаты. '
                        'Доступные поля: - .'
                    ),
                ),
                OpenApiParameter(
                    'search',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Поиск по названию, локальному названию языков. '
                        'Пример использования: `api/languages/?search=English`.'
                    ),
                ),
            ],
        },
        'language_cover_choices_retrieve': {
            'summary': 'Просмотр доступных картинок для обложки изучаемого языка',
            'description': (
                'Возвращает список доступных картинок для смены обложки выбранного '
                'изучаемого языка. '
                'Требуется авторизация.'
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageCoverImageSerailizer(many=True),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'language_cover_set': {
            'summary': 'Обновление обложки изучаемого языка',
            'description': (
                'Обновляет обложку выбранного изучаемого языка картинкой с переданным '
                'id. '
                'Требуется авторизация.'
            ),
            'responses': {
                status.HTTP_201_CREATED: OpenApiResponse(
                    response=LearningLanguageSerailizer,
                    examples=[
                        OpenApiExample(
                            name='no words',
                            value={
                                'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
                                'slug': 'e6EyeJGM7ggQyxhj54SMb6J8Ni3B4IZZo8',
                                'language': {
                                    'id': 'string',
                                    'name': 'string',
                                    'name_local': 'string',
                                    'flag_icon': 'string',
                                },
                                'level': 'string',
                                'cover': 'link/to/image.jpg',
                                'cover_height': 2500,
                                'cover_width': 2500,
                                'words_count': 0,
                                'inactive_words_count': 0,
                                'active_words_count': 0,
                                'mastered_words_count': 0,
                                'words': [],
                            },
                        ),
                    ],
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        # other methods
    },
}
