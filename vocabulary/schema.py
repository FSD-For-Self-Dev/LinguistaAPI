# Описание эндпоинтов в схеме апи

from drf_spectacular.openapi import AutoSchema
from rest_framework import status

from .serializers import WordShortSerializer, WordSerializer, TranslationSerializer, DefinitionSerializer, UsageExampleSerializer, TypeSerializer, FormsGroupSerializer, CollectionSerializer, CollectionsListSerializer, CollectionShortSerializer
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
)

data = {
    'default': {
        'tags': ['authentication'],
    },
    'WordViewSet': {
        'tags': ['vocabulary'],
        'words_list': {
            'summary': 'Просмотр списка слов из своего словаря',
            'description': (
                'Просмотреть список своих слов с пагинацией и применением '
                'фильтров, сортировки и поиска. Нужна авторизация.'
            ),
            'responses': {status.HTTP_200_OK: WordShortSerializer},
            'parameters': [
                OpenApiParameter(
                    'created',
                    OpenApiTypes.DATETIME,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по дате добавления. Включая сравнение больше и '
                        'меньше: created__gt и created__lt.'
                    ),
                ),
                OpenApiParameter(
                    'created__year',
                    OpenApiTypes.INT,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по году добавления. Включая сравнение больше и '
                        'меньше: created__year__gt и created__year__lt.'
                    ),
                ),
                OpenApiParameter(
                    'created__month',
                    OpenApiTypes.INT,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по месяцу добавления. Включая сравнение больше и '
                        'меньше: created__month__gt и created__month__lt.'
                    ),
                ),
                OpenApiParameter(
                    'language',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=('Фильтр по языку. Принимает isocode языка.'),
                ),
                OpenApiParameter(
                    'is_problematic',
                    OpenApiTypes.BOOL,
                    OpenApiParameter.QUERY,
                    description=('Фильтр по метке "проблемное".'),
                ),
                OpenApiParameter(
                    'tags',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по тегам. Принимает name тегов через запятую, '
                        'если несколько.'
                    ),
                ),
                OpenApiParameter(
                    'activity',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по статусу активности. Принимает варианты '
                        'INACTIVE, ACTIVE, MASTERED.'
                    ),
                ),
                OpenApiParameter(
                    'types',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по типам. Принимает slug типов через запятую, '
                        'если несколько.'
                    ),
                ),
                OpenApiParameter(
                    'first_letter',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=('Фильтр по первой букве слова.'),
                ),
                OpenApiParameter(
                    'translations_count',
                    OpenApiTypes.INT,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по кол-ву переводов. Включая сравнение больше и '
                        'меньше: translations_count__gt и translations_count__lt.'
                    ),
                ),
                OpenApiParameter(
                    'examples_count',
                    OpenApiTypes.INT,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по кол-ву примеров. Включая сравнение больше и '
                        'меньше: examples_count__gt и examples_count__lt.'
                    ),
                ),
            ],
        },
        'word_create': {
            'summary': 'Добавление нового слова в свой словарь',
            'request': WordSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_retrieve': {
            'summary': 'Просмотр профиля слова',
            'responses': {
                status.HTTP_200_OK: WordSerializer,
            },
        },
        'word_partial_update': {
            'summary': 'Редактирование слова из своего словаря',
            'responses': {
                status.HTTP_200_OK: WordSerializer,
            },
        },
        'word_destroy': {
            'summary': 'Удаление слова из своего словаря',
            'responses': {
                status.HTTP_204_NO_CONTENT: None,
            },
        },
        'word_random': {
            'summary': 'Получить случайное слово из своего словаря',
        },
        'translations_list': {
            'summary': 'Просмотр списка всех переводов слова',
            'responses': {
                status.HTTP_200_OK: TranslationSerializer,
            },
        },
        'translation_create': {
            'summary': 'Добавление нового перевода к слову',
            'request': TranslationSerializer,
            'responses': {
                status.HTTP_201_CREATED: TranslationSerializer,
            },
        },
        'translations_retrieve': {
            'summary': 'Просмотр перевода слова',
            'responses': {
                status.HTTP_200_OK: TranslationSerializer,
            },
        },
        'translation_partial_update': {
            'summary': 'Редактирование перевода слова',
            'request': TranslationSerializer,
            'responses': {
                status.HTTP_200_OK: TranslationSerializer,
            },
        },
        'translation_destroy': {
            'summary': 'Удаление перевода слова',
            'responses': {
                status.HTTP_204_NO_CONTENT: None,
            },
        },
        'definitions_list': {
            'summary': 'Просмотр списка всех определений слова',
            'responses': {
                status.HTTP_200_OK: DefinitionSerializer,
            },
        },
        'definition_create': {
            'summary': 'Добавление нового определения к слову',
            'request': DefinitionSerializer,
            'responses': {
                status.HTTP_201_CREATED: DefinitionSerializer,
            },
        },
        'definition_retrieve': {
            'summary': 'Просмотр определения слова',
            'responses': {
                status.HTTP_200_OK: DefinitionSerializer,
            },
        },
        'definition_partial_update': {
            'summary': 'Редактирование определения слова',
            'request': DefinitionSerializer,
            'responses': {
                status.HTTP_200_OK: DefinitionSerializer,
            },
        },
        'definition_destroy': {
            'summary': 'Удаление определения слова',
            'responses': {
                status.HTTP_204_NO_CONTENT: None,
            },
        },
        'examples_list': {
            'summary': 'Просмотр списка всех примеров использования слова',
            'responses': {
                status.HTTP_200_OK: UsageExampleSerializer,
            },
        },
        'example_create': {
            'summary': 'Добавление нового примера использования к слову',
            'request': UsageExampleSerializer,
            'responses': {
                status.HTTP_201_CREATED: UsageExampleSerializer,
            },
        },
        'example_retrieve': {
            'summary': 'Просмотр примера использования слова',
            'responses': {
                status.HTTP_200_OK: UsageExampleSerializer,
            },
        },
        'example_partial_update': {
            'summary': 'Редактирование примера использования слова',
            'request': UsageExampleSerializer,
            'responses': {
                status.HTTP_200_OK: UsageExampleSerializer,
            },
        },
        'example_destroy': {
            'summary': 'Удаление примера использования слова',
            'responses': {
                status.HTTP_204_NO_CONTENT: None,
            },
        },
        'problematic_toggle': {
            'summary': 'Изменить метку "проблемное" у слова',
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
            'summary': ('Просмотр списка всех возможных типов и частей речи слов и фраз'),
            'responses': {
                status.HTTP_200_OK: TypeSerializer,
            },
        },
        # other methods
    },
    'FormsGroupsViewSet': {
        'tags': ['forms-groups'],
        'formsgroups_list': {
            'summary': 'Просмотр списка всех групп форм пользователя',
            'responses': {
                status.HTTP_200_OK: FormsGroupSerializer,
            },
        },
        # other methods
    },
    'CollectionViewSet': {
        'tags': ['collections'],
        'collections_list': {
            'summary': 'Просмотр списка всех коллекций пользователя',
            'responses': {
                status.HTTP_200_OK: CollectionSerializer,
            },
        },
        'collection_create': {
            'summary': 'Добавление новой коллекции',
            'request': CollectionSerializer,
            'responses': {
                status.HTTP_201_CREATED: CollectionSerializer,
            },
        },
        'collection_retrieve': {
            'summary': 'Просмотр коллекции',
            'responses': {
                status.HTTP_200_OK: CollectionSerializer,
            },
        },
        'collection_partial_update': {
            'summary': 'Редактирование коллекции',
            'responses': {
                status.HTTP_200_OK: CollectionSerializer,
            },
        },
        'collection_destroy': {
            'summary': 'Удаление коллекции',
            'responses': {
                status.HTTP_204_NO_CONTENT: None,
            },
        },
        'collection_favorite_create': {
            'summary': 'Добавление коллекции в избранное',
        },
        'collection_favorite_destroy': {
            'summary': 'Удаление коллекции из избранного',
        },
        'collections_favorite_list': {
            'summary': 'Cписок избранных коллекций',
            'request': None,
            'responses': {
                status.HTTP_201_CREATED: CollectionShortSerializer,
            },
        },
        'collections_favorite_list_create': {
            'summary': 'Добавление списка коллекций в избранное',
            'request': CollectionsListSerializer,
            # 'responses': {
            #     status.HTTP_201_CREATED: {
            #         'created': int,
            #         'added_to_favorites': collections_titles,
            #     },
            # },
        },
        # other methods
    },
    # other viewsets
}


class CustomSchema(AutoSchema):
    def get_tags(self):
        try:
            return data[self.view.__class__.__name__]['tags']
        except KeyError:
            return data['default']['tags']

    def get_description(self):
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()]['description']
        except KeyError:
            return None

    def get_summary(self):
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()]['summary']
        except KeyError:
            return None
    
    def get_request_serializer(self):
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()]['request']
        except KeyError:
            return None

    def get_responses(self):
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()]['responses']
        except KeyError:
            return None

    def get_override_parameters(self):
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()]['parameters']
        except KeyError:
            return []
