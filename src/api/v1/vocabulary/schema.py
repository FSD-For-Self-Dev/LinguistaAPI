"""Vocabulary schema data."""

from rest_framework import status
from rest_framework.serializers import (
    CharField,
    IntegerField,
    ListField,
)
from drf_spectacular.utils import (
    OpenApiResponse,
    inline_serializer,
)

from api.v1.schema.responses import unauthorized_response, pagination_parameters
from api.v1.schema.utils import get_validation_error_response, get_conflict_response
from api.v1.vocabulary.serializers import (
    WordStandartCardSerializer,
    WordSerializer,
    WordShortCreateSerializer,
    WordTranslationInLineSerializer,
    DefinitionInLineSerializer,
    UsageExampleInLineSerializer,
    TypeSerializer,
    FormGroupListSerializer,
    CollectionSerializer,
    CollectionShortSerializer,
    CollectionListSerializer,
    MultipleWordsSerializer,
    TagListSerializer,
    ImageListSerializer,
    ImageInLineSerializer,
    QuoteInLineSerializer,
    SynonymSerializer,
    AntonymSerializer,
    SimilarSerializer,
    WordTranslationListSerializer,
    WordTranslationCreateSerializer,
    WordTranslationSerializer,
    UsageExampleListSerializer,
    UsageExampleCreateSerializer,
    UsageExampleSerializer,
    DefinitionListSerializer,
    DefinitionCreateSerializer,
    DefinitionSerializer,
    SynonymForWordListSerializer,
    SynonymInLineSerializer,
    AntonymForWordListSerializer,
    AntonymInLineSerializer,
    FormForWordListSerializer,
    FormInLineSerializer,
    SimilarForWordListSerializer,
    SimilarInLineSerializer,
    MainPageSerailizer,
)

from .schema_examples import (
    word_standart_cards_example,
    word_short_cards_example,
    word_long_cards_example,
    words_filters_parameters,
    words_ordering_parameter,
    words_search_parameter,
    word_validation_errors_examples,
    word_types_amount_limit_example,
    word_already_exists_conflict_example,
    collection_validation_errors_examples,
    translation_validation_errors_examples,
    definition_validation_errors_examples,
    example_validation_errors_examples,
    image_validation_errors_examples,
    quote_validation_errors_examples,
)


data = {
    'MainPageViewSet': {
        'tags': ['main_page'],
        'main_page_retrieve': {
            'summary': 'Просмотр главной страницы',
            'description': (
                'Возвращает данные для отображения главной страницы. '
                'Требуется авторизация.'
            ),
            'responses': {
                status.HTTP_200_OK: MainPageSerailizer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        # other methods
    },
    'WordViewSet': {
        'tags': ['vocabulary'],
        'words_list': {
            'summary': 'Просмотр списка слов из словаря пользователя',
            'description': (
                'Возвращает список слов из словаря текущего пользователя '
                'с пагинацией, фильтрами, сортировой и поиском. '
                'Требуется авторизация.'
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: OpenApiResponse(
                    response=WordStandartCardSerializer(many=True),
                    description='Успешный ответ.',
                    examples=[
                        word_standart_cards_example,
                        word_short_cards_example,
                        word_long_cards_example,
                    ],
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
            'parameters': [
                *pagination_parameters,
                *words_filters_parameters,
                words_ordering_parameter,
                words_search_parameter,
            ],
        },
        'word_create': {
            'summary': 'Добавление нового слова в свой словарь',
            'description': 'Возвращает профиль созданного слова. Требуется авторизация.',
            'request': WordSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=word_validation_errors_examples,
                ),
                status.HTTP_409_CONFLICT: get_conflict_response(
                    examples=[
                        word_types_amount_limit_example,
                        word_already_exists_conflict_example,
                    ]
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_retrieve': {
            'summary': 'Просмотр профиля слова',
            'description': ('Возвращает все данные слова. Требуется авторизация. '),
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_partial_update': {
            'summary': 'Редактирование слова из своего словаря',
            'description': (
                'Возвращает обновленные данные слова. Требуется авторизация. '
            ),
            'request': WordSerializer,
            'responses': {
                status.HTTP_200_OK: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=word_validation_errors_examples,
                ),
                status.HTTP_409_CONFLICT: get_conflict_response(
                    examples=[
                        word_types_amount_limit_example,
                        word_already_exists_conflict_example,
                    ]
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_destroy': {
            'summary': 'Удаление слова из своего словаря',
            'description': (
                'Удаляет слово из словаря пользователя. '
                'Возвращает обновленный словарь пользователя. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='paginated_words',
                    fields={
                        'count': IntegerField(default=123),
                        'next': CharField(
                            default='http://api.example.org/accounts/?page=4'
                        ),
                        'previous': CharField(
                            default='http://api.example.org/accounts/?page=2'
                        ),
                        'results': WordStandartCardSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_random': {
            'summary': 'Получить случайное слово из своего словаря',
            'description': (
                'Возвращает данные случайного слова из словаря пользователя. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordStandartCardSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_problematic_toggle': {
            'summary': 'Изменить метку "проблемное" у слова',
            'description': (
                'Изменяет метку "проблемное" слова с True на False и наоборот.'
                'Возвращает обновленные данные слова. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_share_link': {
            'summary': 'Поделиться словом',
            'description': (
                'Возвращает ссылку для получения доступа к данным слова. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='get_share_link',
                    fields={
                        'link': CharField(),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_share': {
            'summary': 'Просмотр профиля слова по ссылке',
            'description': 'Возвращает данные слова.',
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordSerializer,
            },
        },
        'word_multiple_create': {
            'summary': 'Создание нескольких слов подряд',
            'description': 'Возвращает обновленный словарь пользователя. ',
            'request': MultipleWordsSerializer,
            'responses': {
                status.HTTP_201_CREATED: inline_serializer(
                    name='paginated_words',
                    fields={
                        'count': IntegerField(default=123),
                        'next': CharField(
                            default='http://api.example.org/accounts/?page=4'
                        ),
                        'previous': CharField(
                            default='http://api.example.org/accounts/?page=2'
                        ),
                        'results': WordStandartCardSerializer(many=True),
                    },
                ),
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=word_validation_errors_examples,
                ),
                status.HTTP_409_CONFLICT: get_conflict_response(
                    examples=[
                        word_types_amount_limit_example,
                        word_already_exists_conflict_example,
                    ]
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_tags_list': {
            'summary': 'Просмотр списка тегов слова',
            'description': (
                'Возвращает список тегов слова и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='tags_list',
                    fields={
                        'count': IntegerField(),
                        'tags': TagListSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_collections_list': {
            'summary': 'Просмотр списка коллекций с этим словом',
            'description': (
                'Возвращает список коллекций, содержащих текущее слово, и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='collections_list',
                    fields={
                        'count': IntegerField(),
                        'collections': CollectionShortSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_collections_add': {
            'summary': 'Добавление слова в коллекции',
            'description': (
                'Передайте список коллекций, в которые необходимо добавить текущее слово. '
                'Добавляет слово в переданные коллекции. '
                'Если коллекции не найдены, создаёт новые. '
                'Возвращает обновленные данные слова. '
                'Требуется авторизация. '
            ),
            'request': CollectionShortSerializer(many=True),
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=collection_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_translations_list': {
            'summary': 'Просмотр списка переводов слова',
            'description': (
                'Возвращает список всех переводов слова и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='translations_list',
                    fields={
                        'count': IntegerField(),
                        'languages': ListField(child=CharField()),
                        'translations': WordTranslationInLineSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_translations_create': {
            'summary': 'Добавление переводов к слову',
            'description': (
                'Передайте список переводов, чтобы добавить их к текущему слову. '
                'Если переводы не найдены, создаёт новые. '
                'Возвращает обновленные данные слова. '
                'Требуется авторизация. '
            ),
            'request': WordTranslationInLineSerializer(many=True),
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=translation_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_translations_retrieve': {
            'summary': 'Просмотр перевода слова',
            'description': (
                'Возвращает данные перевода слова. ' 'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordTranslationInLineSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_translation_partial_update': {
            'summary': 'Редактирование перевода слова',
            'description': (
                'Возвращает обновленные данные перевода слова. '
                'Требуется авторизация. '
            ),
            'request': WordTranslationInLineSerializer,
            'responses': {
                status.HTTP_200_OK: WordTranslationInLineSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=translation_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_translation_destroy': {
            'summary': 'Удаление перевода слова',
            'description': (
                'Возвращает обновленный список переводов слова. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='translations_list_after_delete',
                    fields={
                        'count': IntegerField(),
                        'translations': WordTranslationInLineSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_definitions_list': {
            'summary': 'Просмотр списка определений слова',
            'description': (
                'Возвращает список всех определений слова и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='definitions_list',
                    fields={
                        'count': IntegerField(),
                        'definitions': DefinitionInLineSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_definitions_create': {
            'summary': 'Добавление определений к слову',
            'description': (
                'Возвращает обновленные данные слова. ' 'Требуется авторизация. '
            ),
            'request': DefinitionInLineSerializer(many=True),
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=definition_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_definition_retrieve': {
            'summary': 'Просмотр определения слова',
            'description': (
                'Возвращает данные определения слова. ' 'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: DefinitionInLineSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_definition_partial_update': {
            'summary': 'Редактирование определения слова',
            'description': (
                'Возвращает обновленные данные определения слова. '
                'Требуется авторизация. '
            ),
            'request': DefinitionInLineSerializer,
            'responses': {
                status.HTTP_200_OK: DefinitionInLineSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=definition_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_definition_destroy': {
            'summary': 'Удаление определения слова',
            'description': (
                'Возвращает обновленный список определений слова. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='definitions_list_after_delete',
                    fields={
                        'count': IntegerField(),
                        'definitions': DefinitionInLineSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_examples_list': {
            'summary': 'Просмотр списка примеров использования слова',
            'description': (
                'Возвращает список всех примеров использования слова и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='examples_list',
                    fields={
                        'count': IntegerField(),
                        'examples': UsageExampleInLineSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_examples_create': {
            'summary': 'Добавление примеров использования к слову',
            'description': (
                'Возвращает обновленные данные слова. ' 'Требуется авторизация. '
            ),
            'request': UsageExampleInLineSerializer(many=True),
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=example_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_example_retrieve': {
            'summary': 'Просмотр примера использования слова',
            'description': (
                'Возвращает данные примера использования слова. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: UsageExampleInLineSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_example_partial_update': {
            'summary': 'Редактирование примера использования слова',
            'description': (
                'Возвращает обновленные данные примера использования слова. '
                'Требуется авторизация. '
            ),
            'request': UsageExampleInLineSerializer,
            'responses': {
                status.HTTP_200_OK: UsageExampleInLineSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=example_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_example_destroy': {
            'summary': 'Удаление примера использования слова',
            'description': (
                'Возвращает обновленный список примеров использования слова. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='examples_list_after_delete',
                    fields={
                        'count': IntegerField(),
                        'examples': UsageExampleInLineSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_synonyms_list': {
            'summary': 'Просмотр списка синонимов слова',
            'description': (
                'Возвращает список всех синонимов слова и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='synonyms_list',
                    fields={
                        'count': IntegerField(),
                        'synonyms': SynonymForWordListSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_synonyms_create': {
            'summary': 'Добавление синонимов к слову',
            'description': (
                'Возвращает обновленные данные слова. ' 'Требуется авторизация. '
            ),
            'request': SynonymForWordListSerializer(many=True),
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=word_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_synonym_retrieve': {
            'summary': 'Просмотр синонима слова',
            'description': (
                'Возвращает данные синонима слова. ' 'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: SynonymInLineSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_synonym_partial_update': {
            'summary': 'Редактирование синонима слова',
            'description': (
                'Возвращает обновленные данные синонима слова. '
                'Требуется авторизация. '
            ),
            'request': SynonymInLineSerializer,
            'responses': {
                status.HTTP_200_OK: SynonymInLineSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=word_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_synonym_destroy': {
            'summary': 'Удаление синонима слова',
            'description': (
                'Удаляет слово из синонимов слова. '
                'Возвращает обновленный список синонимов. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='synonyms_list_after_delete',
                    fields={
                        'count': IntegerField(),
                        'synonyms': SynonymForWordListSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_antonyms_list': {
            'summary': 'Просмотр всех антонимов слова',
            'description': (
                'Возвращает список всех антонимов слова и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='antonyms_list',
                    fields={
                        'count': IntegerField(),
                        'antonyms': AntonymForWordListSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_antonyms_create': {
            'summary': 'Добавление новых антонимов к слову',
            'description': (
                'Возвращает обновленные данные слова. ' 'Требуется авторизация. '
            ),
            'request': AntonymForWordListSerializer(many=True),
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=word_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_antonym_retrieve': {
            'summary': 'Просмотр антонима слова',
            'description': (
                'Возвращает данные антонима слова. ' 'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: AntonymInLineSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_antonym_partial_update': {
            'summary': 'Редактирование антонима слова',
            'description': (
                'Возвращает обновленные данные антонима слова. '
                'Требуется авторизация. '
            ),
            'request': AntonymInLineSerializer,
            'responses': {
                status.HTTP_200_OK: AntonymInLineSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=word_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_antonym_destroy': {
            'summary': 'Удаление антонима слова',
            'description': (
                'Удаляет слово из антонимов слова. '
                'Возвращает обновленный список антонимов. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='antonyms_list_after_delete',
                    fields={
                        'count': IntegerField(),
                        'antonyms': AntonymForWordListSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_forms_list': {
            'summary': 'Просмотр всех форм слова',
            'description': (
                'Возвращает список всех форм слова и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='forms_list',
                    fields={
                        'count': IntegerField(),
                        'forms': FormForWordListSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_forms_create': {
            'summary': 'Добавление новых форм к слову',
            'description': (
                'Возвращает обновленные данные слова. ' 'Требуется авторизация. '
            ),
            'request': FormForWordListSerializer(many=True),
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=word_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_form_retrieve': {
            'summary': 'Просмотр формы слова',
            'description': (
                'Возвращает данные формы слова. ' 'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: FormInLineSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_form_partial_update': {
            'summary': 'Редактирование формы слова',
            'description': (
                'Возвращает обновленные данные формы слова. ' 'Требуется авторизация. '
            ),
            'request': FormInLineSerializer,
            'responses': {
                status.HTTP_200_OK: FormInLineSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=word_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_form_destroy': {
            'summary': 'Удаление формы слова',
            'description': (
                'Удаляет слово из форм слова. '
                'Возвращает обновленный список форм. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='forms_list_after_delete',
                    fields={
                        'count': IntegerField(),
                        'forms': FormForWordListSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_similars_list': {
            'summary': 'Просмотр всех похожих слов слова',
            'description': (
                'Возвращает список всех похожих слов и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='similars_list',
                    fields={
                        'count': IntegerField(),
                        'similars': SimilarForWordListSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_similars_create': {
            'summary': 'Добавление новых похожих слов к слову',
            'description': (
                'Возвращает обновленные данные слова. ' 'Требуется авторизация. '
            ),
            'request': SimilarForWordListSerializer(many=True),
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=word_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_similar_retrieve': {
            'summary': 'Просмотр похожего слова слова',
            'description': (
                'Возвращает данные похожего слова. ' 'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: SimilarInLineSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_similar_partial_update': {
            'summary': 'Редактирование похожего слова слова',
            'description': (
                'Возвращает обновленные данные похожего слова. '
                'Требуется авторизация. '
            ),
            'request': SimilarInLineSerializer,
            'responses': {
                status.HTTP_200_OK: SimilarInLineSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=word_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_similar_destroy': {
            'summary': 'Удаление похожего слова слова',
            'description': (
                'Удаляет слово из похожих слов. '
                'Возвращает обновленный список похожих слов. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='similars_list_after_delete',
                    fields={
                        'count': IntegerField(),
                        'similars': SimilarForWordListSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_associations_list': {
            'summary': 'Просмотр всех ассоциаций слова',
            'description': (
                'Возвращает список всех ассоциаций и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: OpenApiResponse(
                    response=inline_serializer(
                        name='associations_list',
                        fields={
                            'count': IntegerField(),
                            'associations': ImageInLineSerializer(
                                many=True
                            ),  # [need fix] or QuoteInLineSerializer
                        },
                    ),
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_images_list': {
            'summary': 'Просмотр списка всех картинок-ассоциаций слова',
            'description': (
                'Возвращает список всех картинок-ассоциаций слова и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='images_list',
                    fields={
                        'count': IntegerField(),
                        'images': ImageInLineSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_images_upload': {
            'summary': 'Загрузка новых картинок-ассоциаций слова',
            'description': (
                'Возвращает обновленные данные слова. ' 'Требуется авторизация. '
            ),
            'request': ImageInLineSerializer(many=True),
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=image_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_image_retrieve': {
            'summary': 'Просмотр картинки-ассоциации слова',
            'description': (
                'Возвращает данные картинки-ассоциации слова. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: ImageInLineSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_image_partial_update': {
            'summary': 'Редактирование картинки-ассоциации слова',
            'description': (
                'Возвращает обновленные данные картинки-ассоциации слова. '
                'Требуется авторизация. '
            ),
            'request': ImageInLineSerializer,
            'responses': {
                status.HTTP_200_OK: ImageInLineSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=image_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_image_destroy': {
            'summary': 'Удаление картинки-ассоциации слова',
            'description': (
                'Удаляет картинку из ассоциаций слова. '
                'Возвращает обновленный список картинок-ассоциаций слова. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='images_list_after_delete',
                    fields={
                        'count': IntegerField(),
                        'images': ImageInLineSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_quotes_list': {
            'summary': 'Просмотр списка всех цитат-ассоциаций слова',
            'description': (
                'Возвращает список всех цитат-ассоциаций слова и их количество. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='quotes_list',
                    fields={
                        'count': IntegerField(),
                        'quotes': QuoteInLineSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_quotes_create': {
            'summary': 'Добавление новых цитат-ассоциаций слова',
            'description': (
                'Возвращает обновленные данные слова. ' 'Требуется авторизация. '
            ),
            'request': QuoteInLineSerializer(many=True),
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=quote_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_quote_retrieve': {
            'summary': 'Просмотр цитаты-ассоциации слова',
            'description': (
                'Возвращает данные цитаты-ассоциации слова. ' 'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: QuoteInLineSerializer,
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_quote_partial_update': {
            'summary': 'Редактирование цитаты-ассоциации слова',
            'description': (
                'Возвращает обновленные данные цитаты-ассоциации слова. '
                'Требуется авторизация. '
            ),
            'request': QuoteInLineSerializer,
            'responses': {
                status.HTTP_200_OK: QuoteInLineSerializer,
                status.HTTP_400_BAD_REQUEST: get_validation_error_response(
                    examples=quote_validation_errors_examples,
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'word_quote_destroy': {
            'summary': 'Удаление цитаты-ассоциации слова',
            'description': (
                'Удаляет цитату из ассоциаций слова. '
                'Возвращает обновленный список цитат-ассоциаций слова. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='quotes_list_after_delete',
                    fields={
                        'count': IntegerField(),
                        'quotes': QuoteInLineSerializer(many=True),
                    },
                ),
                status.HTTP_401_UNAUTHORIZED: unauthorized_response,
            },
        },
        'words_favorites_list': {
            'summary': 'Просмотр списка избранных слов',
            'description': (
                'Возвращает список избранных слов '
                'с пагинацией, фильтрами, сортировой и поиском. '
                'Принимает те же параметры, что и список слов. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='paginated_favorite_words',
                    fields={
                        'count': IntegerField(default=123),
                        'next': CharField(
                            default='http://api.example.org/accounts/?page=4'
                        ),
                        'previous': CharField(
                            default='http://api.example.org/accounts/?page=2'
                        ),
                        'results': WordStandartCardSerializer(many=True),
                    },
                ),
            },
        },
        'word_favorite_create': {
            'summary': 'Добавление слова в избранное',
            'description': (
                'Добавляет выбранное слово в список избранных слов. '
                'Возвращает обновленные данные слова. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_favorite_destroy': {
            'summary': 'Удаление слова из избранного',
            'description': (
                'Удаляет выбранное слово из списка избранных слов. '
                'Возвращает обновленные данные слова. '
                'Требуется авторизация. '
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordSerializer,
            },
        },
        # other methods
    },
    'TypeViewSet': {
        'tags': ['types'],
        'types_list': {
            'summary': (
                'Просмотр списка всех возможных типов и частей речи слов и фраз'
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: TypeSerializer,
            },
        },
        # other methods
    },
    'TagViewSet': {
        'tags': ['tags'],
        'user_tags_list': {
            'summary': 'Просмотр всех тегов пользователя',
            'request': None,
            'responses': {
                status.HTTP_200_OK: TagListSerializer,
            },
        },
        # other methods
    },
    'FormGroupsViewSet': {
        'tags': ['forms-groups'],
        'formsgroups_list': {
            'summary': 'Просмотр списка всех групп форм пользователя',
            'request': None,
            'responses': {
                status.HTTP_200_OK: FormGroupListSerializer,
            },
        },
        # other methods
    },
    'WordTranslationViewSet': {
        'tags': ['words_translations'],
        'translations_list': {
            'summary': 'Просмотр всех переводов слов пользователя',
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordTranslationListSerializer,
            },
        },
        'translations_create': {
            'summary': 'Создание перевода',
            'request': WordTranslationCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordTranslationSerializer,
            },
        },
        'translation_retrieve': {
            'summary': 'Просмотр перевода и связанных слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordTranslationSerializer,
            },
        },
        'translation_partial_update': {
            'summary': 'Редактирование перевода',
            'request': WordTranslationSerializer,
            'responses': {
                status.HTTP_200_OK: WordTranslationSerializer,
            },
        },
        'translation_destroy': {
            'summary': 'Удаление перевода',
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordTranslationListSerializer,
            },
        },
        'words_add_to_translation': {
            'summary': 'Добавление перевода к словам',
            'request': WordShortCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordTranslationSerializer,
            },
        },
        # other methods
    },
    'UsageExampleViewSet': {
        'tags': ['usage_examples'],
        'examples_list': {
            'summary': 'Просмотр всех примеров использования слов пользователя',
            'request': None,
            'responses': {
                status.HTTP_200_OK: UsageExampleListSerializer,
            },
        },
        'examples_create': {
            'summary': 'Создание примера',
            'request': UsageExampleCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: UsageExampleSerializer,
            },
        },
        'example_retrieve': {
            'summary': 'Просмотр примера и связанных слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: UsageExampleSerializer,
            },
        },
        'example_partial_update': {
            'summary': 'Редактирование примера',
            'request': UsageExampleSerializer,
            'responses': {
                status.HTTP_200_OK: UsageExampleSerializer,
            },
        },
        'example_destroy': {
            'summary': 'Удаление примера',
            'request': None,
            'responses': {
                status.HTTP_200_OK: UsageExampleListSerializer,
            },
        },
        'words_add_to_example': {
            'summary': 'Добавление примера к словам',
            'request': WordShortCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: UsageExampleSerializer,
            },
        },
        # other methods
    },
    'DefinitionViewSet': {
        'tags': ['definitions'],
        'definitions_list': {
            'summary': 'Просмотр всех определений слов пользователя',
            'request': None,
            'responses': {
                status.HTTP_200_OK: DefinitionListSerializer,
            },
        },
        'definitions_create': {
            'summary': 'Создание определения',
            'request': DefinitionCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: DefinitionSerializer,
            },
        },
        'definition_retrieve': {
            'summary': 'Просмотр определения и связанных слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: DefinitionSerializer,
            },
        },
        'definition_partial_update': {
            'summary': 'Редактирование определения',
            'request': DefinitionSerializer,
            'responses': {
                status.HTTP_200_OK: DefinitionSerializer,
            },
        },
        'definition_destroy': {
            'summary': 'Удаление определения',
            'request': None,
            'responses': {
                status.HTTP_200_OK: DefinitionListSerializer,
            },
        },
        'words_add_to_definition': {
            'summary': 'Добавление определения к словам',
            'request': WordShortCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: DefinitionSerializer,
            },
        },
        # other methods
    },
    'AssociationViewSet': {
        'tags': ['associations'],
        'associations_list': {
            'summary': 'Просмотр списка всех ассоциаций из словаря пользователя',
            'request': None,
            # responses
        },
        # other methods
    },
    'ImageViewSet': {
        'tags': ['image_associations'],
        'images_list': {
            'summary': 'Просмотр списка всех картинок-ассоциаций (галерея)',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ImageListSerializer,
            },
        },
        'image_retrieve': {
            'summary': 'Просмотр картинки-ассоциации и связанных слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ImageInLineSerializer,
            },
        },
        'image_partial_update': {
            'summary': 'Редактирование картинки-ассоциации',
            'request': ImageInLineSerializer,
            'responses': {
                status.HTTP_200_OK: ImageInLineSerializer,
            },
        },
        'image_destroy': {
            'summary': 'Удаление картинки-ассоциации',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ImageListSerializer,
            },
        },
        'words_add_to_image': {
            'summary': 'Добавление картинки-ассоциации к словам',
            'request': WordShortCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: ImageInLineSerializer,
            },
        },
        # other methods
    },
    'QuoteViewSet': {
        'tags': ['quote_associations'],
        'quote_retrieve': {
            'summary': 'Просмотр цитаты-ассоциации и связанных слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: QuoteInLineSerializer,
            },
        },
        'quote_partial_update': {
            'summary': 'Редактирование цитаты-ассоциации',
            'request': QuoteInLineSerializer,
            'responses': {
                status.HTTP_200_OK: QuoteInLineSerializer,
            },
        },
        'quote_destroy': {
            'summary': 'Удаление цитаты-ассоциации',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: None,
            },
        },
        'words_add_to_quote': {
            'summary': 'Добавление цитаты-ассоциации к словам',
            'request': WordShortCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: QuoteInLineSerializer,
            },
        },
        # other methods
    },
    'SynonymViewSet': {
        'tags': ['synonyms'],
        'synonym_retrieve': {
            'summary': 'Просмотр синонима и связанных слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SynonymSerializer,
            },
        },
        'synonym_partial_update': {
            'summary': 'Редактирование синонима',
            'request': WordSerializer,
            'responses': {
                status.HTTP_200_OK: WordSerializer,
            },
        },
        'synonym_destroy': {
            'summary': 'Удаление синонима',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: None,
            },
        },
        'words_add_to_synonym': {
            'summary': 'Добавление синонима к словам',
            'request': WordShortCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: SynonymSerializer,
            },
        },
        # other methods
    },
    'AntonymViewSet': {
        'tags': ['antonyms'],
        'antonym_retrieve': {
            'summary': 'Просмотр антонима и связанных слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: AntonymSerializer,
            },
        },
        'antonym_partial_update': {
            'summary': 'Редактирование антонима',
            'request': WordSerializer,
            'responses': {
                status.HTTP_200_OK: WordSerializer,
            },
        },
        'antonym_destroy': {
            'summary': 'Удаление антонима',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: None,
            },
        },
        'words_add_to_antonym': {
            'summary': 'Добавление антонима к словам',
            'request': WordShortCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: AntonymSerializer,
            },
        },
        # other methods
    },
    'SimilarViewSet': {
        'tags': ['similars'],
        'similar_retrieve': {
            'summary': 'Просмотр похожего слова и связанных слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SimilarSerializer,
            },
        },
        'similar_partial_update': {
            'summary': 'Редактирование похожего слова',
            'request': WordSerializer,
            'responses': {
                status.HTTP_200_OK: WordSerializer,
            },
        },
        'similar_destroy': {
            'summary': 'Удаление похожего слова',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: None,
            },
        },
        'words_add_to_similar': {
            'summary': 'Добавление похожего слова к словам',
            'request': WordShortCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: SimilarSerializer,
            },
        },
        # other methods
    },
    'CollectionViewSet': {
        'tags': ['collections'],
        'collections_list': {
            'summary': 'Просмотр списка всех коллекций пользователя',
            'request': None,
            'responses': {
                status.HTTP_200_OK: CollectionListSerializer(many=True),
            },
        },
        'collection_create': {
            'summary': 'Создание новой коллекции',
            'request': CollectionSerializer,
            'responses': {
                status.HTTP_201_CREATED: CollectionSerializer,
            },
        },
        'collection_retrieve': {
            'summary': 'Просмотр коллекции',
            'request': None,
            'responses': {
                status.HTTP_200_OK: CollectionSerializer,
            },
        },
        'collection_partial_update': {
            'summary': 'Редактирование коллекции',
            'request': CollectionSerializer,
            'responses': {
                status.HTTP_200_OK: CollectionSerializer,
            },
        },
        'collection_destroy': {
            'summary': 'Удаление коллекции',
            'request': None,
            'responses': {
                status.HTTP_200_OK: CollectionShortSerializer,
            },
        },
        'words_add_to_collection': {
            'summary': 'Добавление слов в коллекцию',
            'request': WordShortCreateSerializer(many=True),
            'responses': {
                status.HTTP_201_CREATED: CollectionSerializer,
            },
        },
        'collection_images_list': {
            'summary': 'Просмотр гелереи (картинок) коллекции',
            'request': None,
            'responses': {
                status.HTTP_200_OK: CollectionSerializer,
            },
        },
        'collection_translations_list': {
            'summary': 'Просмотр всех переводов слов в коллекции',
            'request': None,
            'responses': {
                status.HTTP_200_OK: CollectionSerializer,
            },
        },
        'collection_definitions_list': {
            'summary': 'Просмотр всех определений слов в коллекции',
            'request': None,
            'responses': {
                status.HTTP_200_OK: CollectionSerializer,
            },
        },
        'collection_examples_list': {
            'summary': 'Просмотр всех примеров использования слов в коллекции',
            'request': None,
            'responses': {
                status.HTTP_200_OK: CollectionSerializer,
            },
        },
        'collections_favorites_list': {
            'summary': 'Просмотр списка избранных коллекций',
            'request': None,
            'responses': {
                status.HTTP_200_OK: inline_serializer(
                    name='paginated_collections',
                    fields={
                        'count': IntegerField(default=123),
                        'next': CharField(
                            default='http://api.example.org/accounts/?page=4'
                        ),
                        'previous': CharField(
                            default='http://api.example.org/accounts/?page=2'
                        ),
                        'results': CollectionShortSerializer(many=True),
                    },
                ),
            },
        },
        'collection_favorite_create': {
            'summary': 'Добавление коллекции в избранное',
            'request': None,
            'responses': {
                status.HTTP_201_CREATED: CollectionShortSerializer,
            },
        },
        'collection_favorite_destroy': {
            'summary': 'Удаление коллекции из избранного',
            'request': None,
            'responses': {
                status.HTTP_200_OK: CollectionShortSerializer,
            },
        },
        'add_words_to_collections': {
            'summary': 'Добавление выбранных слов в выбранные коллекции',
            'request': MultipleWordsSerializer,
            'responses': {
                status.HTTP_201_CREATED: CollectionShortSerializer,
            },
        },
        # other methods
    },
}
