"""Vocabulary schema data examples."""

from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    OpenApiExample,
)

from api.v1.vocabulary.utils import WORD_CARD_TYPES
from apps.vocabulary.models import Word
from apps.vocabulary.constants import VocabularyLengthLimits
from apps.core.constants import REGEX_TEXT_MASK_DETAIL, ExceptionDetails


word_standart_cards_example = OpenApiExample(
    name='standart_cards',
    description='Стандартный вид карточек (?cards_type=standart query param).',
    value=[
        {
            'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            'slug': 'A-FcLKEPQKGWwNcy5AcEUVoHuYQ0qW4FumUxyizq4',
            'language': 'string',
            'text': 'string',
            'author': 'string',
            'created': '2024-09-11T09:36:28.722Z',
            'modified': '2024-09-11T09:36:28.722Z',
            'favorite': True,
            'is_problematic': True,
            'activity_status': 'string',
            'activity_progress': 0,
            'last_exercise_date': '2024-09-11T09:36:28.722Z',
            'translations_count': 0,
            'translations': 'string',
            'image': 'string',
        }
    ],
)


word_short_cards_example = OpenApiExample(
    name='short_cards',
    description='Короткий вид карточек (?cards_type=short query param).',
    value=[
        {
            'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            'slug': '6o4JFSVV9RPY-KHU7rYo2NeGvla56lq1G791FPMbBzNxloMW-pkqjUX5EZCEIhNHIlAUTApgWHD8iCCNJl1f4-thK1XstD',
            'language': 'string',
            'text': 'string',
            'author': 'string',
            'created': '2024-09-11T09:46:12.991Z',
            'modified': '2024-09-11T09:46:12.991Z',
            'favorite': True,
            'is_problematic': True,
            'activity_status': 'string',
            'activity_progress': 0,
            'last_exercise_date': '2024-09-11T09:46:12.991Z',
        }
    ],
)


word_long_cards_example = OpenApiExample(
    name='long_cards',
    description='Длинный вид карточек (?cards_type=long query param).',
    value=[
        {
            'id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
            'slug': '5vGbGAvkFOdhoWIsgf6v6RcOimNe',
            'language': 'string',
            'text': 'string',
            'author': 'string',
            'created': '2024-09-11T09:47:37.042Z',
            'modified': '2024-09-11T09:47:37.042Z',
            'favorite': True,
            'is_problematic': True,
            'activity_status': 'string',
            'activity_progress': 0,
            'last_exercise_date': '2024-09-11T09:47:37.042Z',
            'last_6_translations': 'string',
            'other_translations_count': 0,
            'image': 'string',
        }
    ],
)


words_filters_parameters = [
    OpenApiParameter(
        'activity_status',
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по статусу активности. Принимает варианты '
            'I: Inactive (Неактивные), '
            'A: Active (Активные), '
            'M: Mastered (Усвоенные).'
        ),
        enum=[activity[0] for activity in Word.ACTIVITY],
    ),
    OpenApiParameter(
        'created__date',
        OpenApiTypes.DATE,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по дате добавления слова. Включая сравнение больше и '
            'меньше: `created__date__gt` и `created__date__lt`. '
            'Формат: YYYY-MM-DD. '
        ),
    ),
    OpenApiParameter(
        'created__year',
        OpenApiTypes.NUMBER,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по году добавления слова. Включая сравнение больше и '
            'меньше: `created__year__gt` и `created__year__lt`. '
            'Формат: YYYY. '
        ),
    ),
    OpenApiParameter(
        'created__month',
        OpenApiTypes.NUMBER,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по месяцу добавления слова. Включая сравнение больше и '
            'меньше: `created__month__gt` и `created__month__lt`. '
            'Формат: MM. '
        ),
    ),
    OpenApiParameter(
        'last_exercise_date__date',
        OpenApiTypes.DATE,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по дате последней тренировки с этим словом. '
            'Включая сравнение больше и меньше: '
            '`last_exercise_date__date__gt` и `last_exercise_date__date__lt`. '
            'Формат: YYYY-MM-DD. '
        ),
    ),
    OpenApiParameter(
        'last_exercise_date__year',
        OpenApiTypes.NUMBER,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по году последней тренировки с этим словом. '
            'Включая сравнение больше и меньше: '
            '`last_exercise_date__year__gt` и `last_exercise_date__year__lt`. '
            'Формат: YYYY. '
        ),
    ),
    OpenApiParameter(
        'last_exercise_date__month',
        OpenApiTypes.NUMBER,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по месяцу последней тренировки с этим словом. '
            'Включая сравнение больше и меньше: '
            '`last_exercise_date__month__gt` и `last_exercise_date__month__lt`. '
            'Формат: MM. '
        ),
    ),
    OpenApiParameter(
        'language',
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по языку. Принимает isocode языка. ' 'Пример: `?language=ru` '
        ),
    ),
    OpenApiParameter(
        'is_problematic',
        OpenApiTypes.BOOL,
        OpenApiParameter.QUERY,
        description=('Фильтр по метке "проблемное".'),
        enum=[True, False],
    ),
    OpenApiParameter(
        'have_associations',
        OpenApiTypes.BOOL,
        OpenApiParameter.QUERY,
        description=('Фильтр по наличию хотя бы одной ассоциации у слова.'),
        enum=[True, False],
    ),
    OpenApiParameter(
        'tags',
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по тегам. Принимает name тегов через запятую, '
            'если несколько. Пример: `?tags=tag1,tag2` '
        ),
    ),
    OpenApiParameter(
        'types',
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по типам. Принимает slug типов через запятую, '
            'если несколько. Пример: `?types=noun,verb` '
        ),
    ),
    OpenApiParameter(
        'first_letter',
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        description=('Фильтр по первой букве слова.'),
    ),
    OpenApiParameter(
        'last_letter',
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        description=('Фильтр по последней букве слова.'),
    ),
    OpenApiParameter(
        'translations_count',
        OpenApiTypes.NUMBER,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по кол-ву переводов. Включая сравнение больше и '
            'меньше: `translations_count__gt` и `translations_count__lt`. '
        ),
    ),
    OpenApiParameter(
        'examples_count',
        OpenApiTypes.NUMBER,
        OpenApiParameter.QUERY,
        description=(
            'Фильтр по кол-ву примеров. Включая сравнение больше и '
            'меньше: `examples_count__gt` и `examples_count__lt`. '
        ),
    ),
    OpenApiParameter(
        'cards_type',
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        description=('Смена вида карточек слов (сериализатора слов). '),
        enum=WORD_CARD_TYPES.keys(),
    ),
]


words_search_parameter = OpenApiParameter(
    'search',
    OpenApiTypes.STR,
    OpenApiParameter.QUERY,
    description=(
        'Поиск по тексту слова, примеров, определений, названию тегов, переводам. '
        'Пример использования: `api/vocabulary/?search=butterfly`. '
    ),
)


words_ordering_parameter = OpenApiParameter(
    'ordering',
    OpenApiTypes.STR,
    OpenApiParameter.QUERY,
    description=(
        'Принимает поле, по которому необходимо сортировать результаты. '
        'Для сортировки по убыванию используется префикс `-`. '
        'Пример использования: `api/vocabulary/?ordering=-translations_count`. '
    ),
    enum=(
        'text',
        'translations_count',
        'last_exercise_date',
        'created',
    ),
)


word_validation_errors_examples = [
    OpenApiExample(
        name='invalid_language',
        value={
            'language': ['Объект с name=Englishh не существует.'],
        },
    ),
    OpenApiExample(
        name='invalid_text',
        value={
            'text': [
                REGEX_TEXT_MASK_DETAIL,
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_WORD_LENGTH} символов.',
            ],
        },
    ),
    OpenApiExample(
        name='tags_empty_name',
        value=[{'name': ['Это поле не может быть пустым.']}],
    ),
    OpenApiExample(
        name='invalid_types',
        value={
            'types': ['Объект с name=string не существует.'],
        },
    ),
    OpenApiExample(
        name='invalid_form_groups',
        value={
            'form_groups': [
                {
                    'name': [
                        REGEX_TEXT_MASK_DETAIL,
                        f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_FORMSGROUP_NAME_LENGTH} символов.',
                    ],
                    'language': ['Объект с name=string не существует.'],
                    'translation': [
                        REGEX_TEXT_MASK_DETAIL,
                        f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_FORMSGROUP_TRANSLATION_LENGTH} символов.',
                    ],
                }
            ],
        },
    ),
    OpenApiExample(
        name='invalid_translations',
        value={
            'translations': [
                {
                    'text': [
                        REGEX_TEXT_MASK_DETAIL,
                        f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_TRANSLATION_LENGTH} символов.',
                    ],
                    'language': ['Объект с name=string не существует.'],
                }
            ],
        },
    ),
    OpenApiExample(
        name='invalid_examples',
        value={
            'examples': [
                {
                    'language': ['Объект с name=string не существует.'],
                    'text': [
                        REGEX_TEXT_MASK_DETAIL,
                        f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_EXAMPLE_LENGTH} символов.',
                    ],
                    'translation': [
                        REGEX_TEXT_MASK_DETAIL,
                        f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_EXAMPLE_LENGTH} символов.',
                    ],
                }
            ],
        },
    ),
    OpenApiExample(
        name='invalid_definitions',
        value={
            'definitions': [
                {
                    'language': ['Объект с name=string не существует.'],
                    'text': [
                        REGEX_TEXT_MASK_DETAIL,
                        f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_DEFINITION_LENGTH} символов.',
                    ],
                    'translation': [
                        REGEX_TEXT_MASK_DETAIL,
                        f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_DEFINITION_LENGTH} символов.',
                    ],
                }
            ],
        },
    ),
    OpenApiExample(
        name='invalid_image_associations',
        value={
            'image_associations': [
                {
                    'image': [
                        ExceptionDetails.Images.INVALID_IMAGE_FILE,
                    ]
                }
            ],
        },
    ),
    OpenApiExample(
        name='invalid_quote_associations',
        value={
            'quote_associations': [
                {
                    'text': [
                        REGEX_TEXT_MASK_DETAIL,
                        f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_QUOTE_TEXT_LENGTH} символов.',
                    ],
                    'quote_author': [
                        REGEX_TEXT_MASK_DETAIL,
                        f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_QUOTE_AUTHOR_LENGTH} символов.',
                    ],
                }
            ],
        },
    ),
    OpenApiExample(
        name='invalid_synonyms',
        value={
            'synonyms': [
                {
                    'from_word': {
                        'language': ['Объект с name=string не существует.'],
                        'text': [
                            REGEX_TEXT_MASK_DETAIL,
                            f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_WORD_LENGTH} символов.',
                        ],
                        'types': ['Объект с name=string не существует.'],
                        'form_groups': [
                            {
                                'name': [
                                    REGEX_TEXT_MASK_DETAIL,
                                    f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_FORMSGROUP_NAME_LENGTH} символов.',
                                ],
                                'language': ['Объект с name=string не существует.'],
                                'translation': [
                                    REGEX_TEXT_MASK_DETAIL,
                                    f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_FORMSGROUP_TRANSLATION_LENGTH} символов.',
                                ],
                            }
                        ],
                        'translations': [
                            {
                                'text': [
                                    REGEX_TEXT_MASK_DETAIL,
                                    f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_TRANSLATION_LENGTH} символов.',
                                ],
                                'language': ['Объект с name=string не существует.'],
                            }
                        ],
                        'examples': [
                            {
                                'language': ['Объект с name=string не существует.'],
                                'text': [
                                    REGEX_TEXT_MASK_DETAIL,
                                    f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_EXAMPLE_LENGTH} символов.',
                                ],
                                'translation': [
                                    REGEX_TEXT_MASK_DETAIL,
                                    f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_EXAMPLE_LENGTH} символов.',
                                ],
                            }
                        ],
                        'definitions': [
                            {
                                'language': ['Объект с name=string не существует.'],
                                'text': [
                                    REGEX_TEXT_MASK_DETAIL,
                                    f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_DEFINITION_LENGTH} символов.',
                                ],
                                'translation': [
                                    REGEX_TEXT_MASK_DETAIL,
                                    f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_DEFINITION_LENGTH} символов.',
                                ],
                            }
                        ],
                        'image_associations': [
                            {'image': ['Invalid image file passed.']}
                        ],
                        'quote_associations': [
                            {
                                'text': [
                                    REGEX_TEXT_MASK_DETAIL,
                                    f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_QUOTE_TEXT_LENGTH} символов.',
                                ],
                                'quote_author': [
                                    REGEX_TEXT_MASK_DETAIL,
                                    f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_QUOTE_AUTHOR_LENGTH} символов.',
                                ],
                            }
                        ],
                    }
                }
            ],
        },
    ),
    OpenApiExample(
        name='invalid_collections',
        value={
            'collections': [
                {
                    'title': [
                        REGEX_TEXT_MASK_DETAIL,
                        f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_COLLECTION_TITLE_LENGTH} символов.',
                    ]
                },
                {
                    'description': [
                        REGEX_TEXT_MASK_DETAIL,
                        f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_COLLECTION_DESCRIPTION_LENGTH} символов.',
                    ]
                },
            ],
        },
    ),
    OpenApiExample(
        name='invalid_note',
        value={
            'note': [
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_NOTE_LENGTH} символов.'
            ],
        },
    ),
]


word_types_amount_limit_example = OpenApiExample(
    name='word_types',
    description='Превышено ограничение количества типов слова.',
    value={
        'exception_code': 'amount_limit_exceeded',
        'detail': 'Word types amount limit exceeded.',
        'amount_limit': 3,
    },
)


word_already_exists_conflict_example = OpenApiExample(
    name='word_already_exist',
    description='Слово с переданными данными уже существует в словаре пользователя.',
    value={
        'exception_code': 'already_exist',
        'detail': 'Такое слово уже есть в вашем словаре. Обновить его?',
        'existing_object': {
            'id': 159786489333265405032252898597390240393,
            'slug': 'text-test_user22',
            'language': 'English',
            'text': 'text',
            'author': {
                'id': '08f6da7b-e2bc-47f9-8ae9-25127ecbae82',
                'username': 'test_user22',
                'first_name': 'Ivan',
                'image': 'http://127.0.0.1:8000/media/users/profile-images/test_user22/de42bf37-81f5-4c90-bdc2-7136f2779155.jpg',
                'image_height': 6433,
                'image_width': 4289,
            },
            'favorite': False,
            'is_problematic': False,
            'note': '',
            'types': [],
            'tags': [],
            'form_groups': [],
            'activity_status': 'Неактивное',
            'translations_count': 0,
            'translations': [],
            'examples_count': 0,
            'examples': [],
            'definitions_count': 0,
            'definitions': [],
            'images_count': 0,
            'images': [],
            'associations_count': 0,
            'associations': [],
            'synonyms_count': 0,
            'synonyms': [],
            'antonyms_count': 0,
            'antonyms': [],
            'forms_count': 0,
            'forms': [],
            'similars_count': 0,
            'similars': [],
            'collections_count': 0,
            'collections': [],
            'created': '2024-09-11 14:03',
            'modified': '2024-09-11 14:03',
        },
    },
)


collection_validation_errors_examples = [
    OpenApiExample(
        name='invalid_title',
        value={
            'title': [
                REGEX_TEXT_MASK_DETAIL,
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_COLLECTION_TITLE_LENGTH} символов.',
            ],
        },
    ),
    OpenApiExample(
        name='invalid_description',
        value={
            'description': [
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_COLLECTION_DESCRIPTION_LENGTH} символов.',
            ],
        },
    ),
]

translation_validation_errors_examples = [
    OpenApiExample(
        name='invalid_text',
        value={
            'text': [
                REGEX_TEXT_MASK_DETAIL,
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_TRANSLATION_LENGTH} символов.',
            ],
        },
    ),
    OpenApiExample(
        name='invalid_language',
        value={
            'language': ['Объект с name=string не существует.'],
        },
    ),
]


definition_validation_errors_examples = [
    OpenApiExample(
        name='invalid_text',
        value={
            'text': [
                REGEX_TEXT_MASK_DETAIL,
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_DEFINITION_LENGTH} символов.',
            ],
        },
    ),
    OpenApiExample(
        name='invalid_language',
        value={
            'language': ['Объект с name=string не существует.'],
        },
    ),
    OpenApiExample(
        name='invalid_translation',
        value={
            'text': [
                REGEX_TEXT_MASK_DETAIL,
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_DEFINITION_LENGTH} символов.',
            ],
        },
    ),
]


example_validation_errors_examples = [
    OpenApiExample(
        name='invalid_text',
        value={
            'text': [
                REGEX_TEXT_MASK_DETAIL,
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_EXAMPLE_LENGTH} символов.',
            ],
        },
    ),
    OpenApiExample(
        name='invalid_language',
        value={
            'language': ['Объект с name=string не существует.'],
        },
    ),
    OpenApiExample(
        name='invalid_translation',
        value={
            'text': [
                REGEX_TEXT_MASK_DETAIL,
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_TRANSLATION_LENGTH} символов.',
            ],
        },
    ),
]


note_validation_errors_examples = [
    OpenApiExample(
        name='invalid_text',
        value={
            'text': [
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_NOTE_LENGTH} символов.',
            ],
        },
    ),
]


image_validation_errors_examples = [
    OpenApiExample(
        name='invalid_file',
        value={
            'image': [
                ExceptionDetails.Images.INVALID_IMAGE_FILE,
            ],
        },
    ),
    OpenApiExample(
        name='empty_file',
        value={
            'non_field_errors': [ExceptionDetails.Images.IMAGE_FILE_OR_URL_IS_REQUIRED],
        },
    ),
    OpenApiExample(
        name='invalid_file_size',
        value={
            'image': [
                ExceptionDetails.Images.INVALID_IMAGE_SIZE,
            ],
        },
    ),
]


quote_validation_errors_examples = [
    OpenApiExample(
        name='invalid_text',
        value={
            'text': [
                REGEX_TEXT_MASK_DETAIL,
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_QUOTE_TEXT_LENGTH} символов.',
            ],
        },
    ),
    OpenApiExample(
        name='invalid_quote_author',
        value={
            'quote_author': [
                REGEX_TEXT_MASK_DETAIL,
                f'Убедитесь, что это значение содержит не более {VocabularyLengthLimits.MAX_QUOTE_AUTHOR_LENGTH} символов.',
            ],
        },
    ),
]
