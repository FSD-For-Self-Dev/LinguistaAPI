"""Custom schema generator."""

from rest_framework import status
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
)

from vocabulary.serializers import (
    WordStandartCardSerializer,
    WordSerializer,
    WordShortCreateSerializer,
    WordTranslationInLineSerializer,
    DefinitionInLineSerializer,
    UsageExampleInLineSerializer,
    TypeSerializer,
    FormsGroupListSerializer,
    CollectionSerializer,
    CollectionShortSerializer,
    MultipleWordsSerializer,
    TagListSerializer,
    LearningLanguageWithLastWordsSerailizer,
    LearningLanguageShortSerailizer,
    ImageShortSerailizer,
    ImageListSerializer,
    ImageInLineSerializer,
    ImageForWordSerializer,
    QuoteInLineSerializer,
    QuoteForWordSerializer,
    SynonymSerializer,
    AntonymSerializer,
    SimilarSerializer,
    WordTranslationListSerializer,
    WordTranslationCreateSerializer,
    WordTranslationForWordSerializer,
    WordTranslationSerializer,
    UsageExampleListSerializer,
    UsageExampleCreateSerializer,
    UsageExampleForWordSerializer,
    UsageExampleSerializer,
    DefinitionListSerializer,
    DefinitionCreateSerializer,
    DefinitionForWordSerializer,
    DefinitionSerializer,
    NoteInLineSerializer,
    NoteForWordSerializer,
    SynonymForWordListSerializer,
    SynonymForWordSerializer,
    AntonymForWordListSerializer,
    AntonymForWordSerializer,
    FormForWordListSerializer,
    FormForWordSerializer,
    SimilarForWordListSerializer,
    SimilarForWordSerailizer,
    AssociationsCreateSerializer,
)
from exercises.serializers import (
    ExerciseListSerializer,
    ExerciseProfileSerializer,
    SetListSerializer,
    SetSerializer,
    LastApproachProfileSerializer,
    CollectionWithAvailableWordsSerializer,
    TranslatorUserDefaultSettingsSerializer,
)
from users.serializers import (
    LearningLanguageSerailizer,
    NativeLanguageSerailizer,
    UserShortSerializer,
)
from languages.serializers import LanguageSerailizer


class CustomSchema(AutoSchema):
    def get_tags(self):
        try:
            return data[self.view.__class__.__name__]['tags']
        except KeyError:
            return data['default']['tags']

    def get_description(self):
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'description'
            ]
        except KeyError:
            return None

    def get_summary(self):
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'summary'
            ]
        except KeyError:
            return None

    def get_request_serializer(self):
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'request'
            ]
        except KeyError:
            return None

    def get_response_serializers(self):
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'responses'
            ]
        except KeyError:
            return {}

    def get_override_parameters(self):
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'parameters'
            ]
        except KeyError:
            return []


data = {
    'default': {
        'tags': ['authentication'],
    },
    'MainPageViewSet': {
        'tags': ['main_page'],
        'main_page_retrieve': {
            'summary': 'Просмотр главной страницы',
        },
        # other methods
    },
    'WordViewSet': {
        'tags': ['vocabulary'],
        'words_list': {
            'summary': 'Просмотр списка слов из своего словаря',
            'description': (
                'Просмотреть список своих слов с пагинацией и применением '
                'фильтров, сортировки и поиска. Нужна авторизация.'
            ),
            'request': None,
            'responses': {
                status.HTTP_200_OK: OpenApiResponse(
                    response=WordStandartCardSerializer,
                    description='Success response via ?view=standart query param',
                ),
                # status.HTTP_200_OK: OpenApiResponse(
                #     response=WordShortCardSerializer,
                #     description='Success response via ?view=short query param'
                # ),
                # status.HTTP_200_OK: OpenApiResponse(
                #     response=WordLongCardSerializer,
                #     description='Success response via ?view=long query param'
                # ),
            },
            'parameters': [
                OpenApiParameter(
                    'activity_status',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по статусу активности. Принимает варианты '
                        'I (для Неактивных (Inactive)), '
                        'A (для Активных (Active)), '
                        'M (для Усвоенных (Mastered)).'
                    ),
                ),
                OpenApiParameter(
                    'created__date',
                    OpenApiTypes.DATE,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по дате добавления слова. Включая сравнение больше и '
                        'меньше: created__date__gt и created__date__lt.'
                    ),
                ),
                OpenApiParameter(
                    'created__year',
                    OpenApiTypes.NUMBER,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по году добавления слова. Включая сравнение больше и '
                        'меньше: created__year__gt и created__year__lt.'
                    ),
                ),
                OpenApiParameter(
                    'created__month',
                    OpenApiTypes.NUMBER,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по месяцу добавления слова. Включая сравнение больше и '
                        'меньше: created__month__gt и created__month__lt.'
                    ),
                ),
                OpenApiParameter(
                    'last_exercise_date__date',
                    OpenApiTypes.DATE,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по дате последней тренировки с этим словом. '
                        'Включая сравнение больше и меньше: '
                        'last_exercise_date__date__gt и last_exercise_date__date__lt.'
                    ),
                ),
                OpenApiParameter(
                    'last_exercise_date__year',
                    OpenApiTypes.NUMBER,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по году последней тренировки с этим словом. '
                        'Включая сравнение больше и меньше: '
                        'last_exercise_date__year__gt и last_exercise_date__year__lt.'
                    ),
                ),
                OpenApiParameter(
                    'last_exercise_date__month',
                    OpenApiTypes.NUMBER,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по месяцу последней тренировки с этим словом. '
                        'Включая сравнение больше и меньше: '
                        'last_exercise_date__month__gt и last_exercise_date__month__lt.'
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
                    'have_associations',
                    OpenApiTypes.BOOL,
                    OpenApiParameter.QUERY,
                    description=('Фильтр по наличию хотя бы одной ассоциации у слова.'),
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
                    OpenApiTypes.NUMBER,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по кол-ву переводов. Включая сравнение больше и '
                        'меньше: translations_count__gt и translations_count__lt.'
                    ),
                ),
                OpenApiParameter(
                    'examples_count',
                    OpenApiTypes.NUMBER,
                    OpenApiParameter.QUERY,
                    description=(
                        'Фильтр по кол-ву примеров. Включая сравнение больше и '
                        'меньше: examples_count__gt и examples_count__lt.'
                    ),
                ),
                OpenApiParameter(
                    'view',
                    OpenApiTypes.STR,
                    OpenApiParameter.QUERY,
                    description=(
                        'Смена вида карточек слов (сериализатора слов), '
                        'принимает значения: standart, long, short.'
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
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordSerializer,
            },
        },
        'word_partial_update': {
            'summary': 'Редактирование слова из своего словаря',
            'request': WordSerializer,
            'responses': {
                status.HTTP_200_OK: WordSerializer,
            },
        },
        'word_destroy': {
            'summary': 'Удаление слова из своего словаря',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: WordStandartCardSerializer,
            },
        },
        'word_random': {
            'summary': 'Получить случайное слово из своего словаря',
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordStandartCardSerializer,
            },
        },
        'word_problematic_toggle': {
            'summary': 'Изменить метку "проблемное" у слова',
            'request': None,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_multiple_create': {
            'summary': 'Создание нескольких слов подряд',
            'request': MultipleWordsSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordStandartCardSerializer,
            },
        },
        'word_tags_list': {
            'summary': 'Просмотр всех тегов слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: TagListSerializer,
            },
        },
        'word_collections_list': {
            'summary': 'Просмотр всех коллекций с этим словом',
            'request': None,
            'responses': {
                status.HTTP_200_OK: CollectionShortSerializer,
            },
        },
        'word_collections_add': {
            'summary': 'Добавление слова в коллекции',
            'request': CollectionShortSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_translations_list': {
            'summary': 'Просмотр всех переводов слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordTranslationInLineSerializer,
            },
        },
        'word_translations_create': {
            'summary': 'Добавление новых переводов к слову',
            'request': WordTranslationInLineSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_translations_retrieve': {
            'summary': 'Просмотр перевода слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordTranslationForWordSerializer,
            },
        },
        'word_translation_partial_update': {
            'summary': 'Редактирование перевода слова',
            'request': WordTranslationForWordSerializer,
            'responses': {
                status.HTTP_200_OK: WordTranslationForWordSerializer,
            },
        },
        'word_translation_destroy': {
            'summary': 'Удаление перевода слова',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: WordTranslationInLineSerializer,
            },
        },
        'word_definitions_list': {
            'summary': 'Просмотр всех определений слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: DefinitionInLineSerializer,
            },
        },
        'word_definitions_create': {
            'summary': 'Добавление новых определений к слову',
            'request': DefinitionInLineSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_definition_retrieve': {
            'summary': 'Просмотр определения слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: DefinitionForWordSerializer,
            },
        },
        'word_definition_partial_update': {
            'summary': 'Редактирование определения слова',
            'request': DefinitionForWordSerializer,
            'responses': {
                status.HTTP_200_OK: DefinitionForWordSerializer,
            },
        },
        'word_definition_destroy': {
            'summary': 'Удаление определения слова',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: DefinitionInLineSerializer,
            },
        },
        'word_examples_list': {
            'summary': 'Просмотр всех примеров использования слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: UsageExampleInLineSerializer,
            },
        },
        'word_examples_create': {
            'summary': 'Добавление новых примеров использования к слову',
            'request': UsageExampleInLineSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_example_retrieve': {
            'summary': 'Просмотр примера использования слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: UsageExampleForWordSerializer,
            },
        },
        'word_example_partial_update': {
            'summary': 'Редактирование примера использования слова',
            'request': UsageExampleForWordSerializer,
            'responses': {
                status.HTTP_200_OK: UsageExampleForWordSerializer,
            },
        },
        'word_example_destroy': {
            'summary': 'Удаление примера использования слова',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: UsageExampleInLineSerializer,
            },
        },
        'word_notes_list': {
            'summary': 'Просмотр всех заметок слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: NoteInLineSerializer,
            },
        },
        'word_notes_create': {
            'summary': 'Добавление новых заметок к слову',
            'request': NoteInLineSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_note_retrieve': {
            'summary': 'Просмотр заметки слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: NoteForWordSerializer,
            },
        },
        'word_note_partial_update': {
            'summary': 'Редактирование заметки слова',
            'request': NoteForWordSerializer,
            'responses': {
                status.HTTP_200_OK: NoteForWordSerializer,
            },
        },
        'word_note_destroy': {
            'summary': 'Удаление заметки слова',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: WordSerializer,
            },
        },
        'word_synonyms_list': {
            'summary': 'Просмотр всех синонимов слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SynonymForWordListSerializer,
            },
        },
        'word_synonyms_create': {
            'summary': 'Добавление новых синонимов к слову',
            'request': SynonymForWordListSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_synonym_retrieve': {
            'summary': 'Просмотр синонима слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SynonymForWordSerializer,
            },
        },
        'word_synonym_partial_update': {
            'summary': 'Редактирование синонима слова',
            'request': SynonymForWordSerializer,
            'responses': {
                status.HTTP_200_OK: SynonymForWordSerializer,
            },
        },
        'word_synonym_destroy': {
            'summary': 'Удаление синонима слова',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: SynonymForWordListSerializer,
            },
        },
        'word_antonyms_list': {
            'summary': 'Просмотр всех антонимов слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: AntonymForWordListSerializer,
            },
        },
        'word_antonyms_create': {
            'summary': 'Добавление новых антонимов к слову',
            'request': AntonymForWordListSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_antonym_retrieve': {
            'summary': 'Просмотр антонима слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: AntonymForWordSerializer,
            },
        },
        'word_antonym_partial_update': {
            'summary': 'Редактирование антонима слова',
            'request': AntonymForWordSerializer,
            'responses': {
                status.HTTP_200_OK: AntonymForWordSerializer,
            },
        },
        'word_antonym_destroy': {
            'summary': 'Удаление антонима слова',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: AntonymForWordListSerializer,
            },
        },
        'word_forms_list': {
            'summary': 'Просмотр всех форм слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: FormForWordListSerializer,
            },
        },
        'word_forms_create': {
            'summary': 'Добавление новых форм к слову',
            'request': FormForWordListSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_form_retrieve': {
            'summary': 'Просмотр формы слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: FormForWordSerializer,
            },
        },
        'word_form_partial_update': {
            'summary': 'Редактирование формы слова',
            'request': FormForWordSerializer,
            'responses': {
                status.HTTP_200_OK: FormForWordSerializer,
            },
        },
        'word_form_destroy': {
            'summary': 'Удаление формы слова',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: FormForWordListSerializer,
            },
        },
        'word_similars_list': {
            'summary': 'Просмотр всех похожих слов слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SimilarForWordListSerializer,
            },
        },
        'word_similars_create': {
            'summary': 'Добавление новых похожих слов к слову',
            'request': SimilarForWordListSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_similar_retrieve': {
            'summary': 'Просмотр похожего слова слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SimilarForWordSerailizer,
            },
        },
        'word_similar_partial_update': {
            'summary': 'Редактирование похожего слова слова',
            'request': SimilarForWordSerailizer,
            'responses': {
                status.HTTP_200_OK: SimilarForWordSerailizer,
            },
        },
        'word_similar_destroy': {
            'summary': 'Удаление похожего слова слова',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: SimilarForWordListSerializer,
            },
        },
        'word_associations_list': {
            'summary': 'Просмотр всех ассоциаций слова',
            'request': None,
            # 'responses'
        },
        'word_associations_create': {
            'summary': 'Добавление новых ассоциаций к слову',
            'request': AssociationsCreateSerializer,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_image_retrieve': {
            'summary': 'Просмотр картинки-ассоциации слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ImageForWordSerializer,
            },
        },
        'word_image_partial_update': {
            'summary': 'Редактирование картинки-ассоциации слова',
            'request': ImageForWordSerializer,
            'responses': {
                status.HTTP_200_OK: ImageForWordSerializer,
            },
        },
        'word_image_destroy': {
            'summary': 'Удаление картинки-ассоциации слова',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: ImageInLineSerializer,
            },
        },
        'word_quote_retrieve': {
            'summary': 'Просмотр цитаты-ассоциации слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: QuoteForWordSerializer,
            },
        },
        'word_quote_partial_update': {
            'summary': 'Редактирование цитаты-ассоциации слова',
            'request': QuoteForWordSerializer,
            'responses': {
                status.HTTP_200_OK: QuoteForWordSerializer,
            },
        },
        'word_quote_destroy': {
            'summary': 'Удаление цитаты-ассоциации слова',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: QuoteInLineSerializer,
            },
        },
        'words_favorites_list': {
            'summary': 'Просмотр списка избранных слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordStandartCardSerializer,
            },
        },
        'word_favorite_create': {
            'summary': 'Добавление слова в избранное',
            'request': None,
            'responses': {
                status.HTTP_201_CREATED: WordSerializer,
            },
        },
        'word_favorite_destroy': {
            'summary': 'Удаление слова из избранного',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: WordSerializer,
            },
        },
        'images_upload': {
            'summary': 'Загрузка картинок-ассоциаций',
            # 'request'
            'responses': {
                status.HTTP_201_CREATED: ImageInLineSerializer,
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
    'FormsGroupsViewSet': {
        'tags': ['forms-groups'],
        'formsgroups_list': {
            'summary': 'Просмотр списка всех групп форм пользователя',
            'request': None,
            'responses': {
                status.HTTP_200_OK: FormsGroupListSerializer,
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
                status.HTTP_204_NO_CONTENT: WordTranslationListSerializer,
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
                status.HTTP_204_NO_CONTENT: UsageExampleListSerializer,
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
                status.HTTP_204_NO_CONTENT: DefinitionListSerializer,
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
        'tags': ['images_associations'],
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
                status.HTTP_204_NO_CONTENT: ImageListSerializer,
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
        'tags': ['quotes_associations'],
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
                status.HTTP_204_NO_CONTENT: CollectionShortSerializer,
            },
        },
        'words_add_to_collection': {
            'summary': 'Добавление слов в коллекцию',
            'request': WordShortCreateSerializer,
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
                status.HTTP_200_OK: CollectionShortSerializer,
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
                status.HTTP_204_NO_CONTENT: CollectionShortSerializer,
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
    'LanguagesViewSet': {
        'tags': ['learning_languages'],
        'learning_languages_list': {
            'summary': 'Просмотр списка изучаемых языков пользователя',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LearningLanguageWithLastWordsSerailizer,
            },
        },
        'learning_language_create': {
            'summary': 'Добавление изучаемого языка',
            'request': LearningLanguageSerailizer,
            'responses': {
                status.HTTP_201_CREATED: LearningLanguageWithLastWordsSerailizer,
            },
        },
        'learning_language_retrieve': {
            'summary': 'Просмотр профиля изучаемого языка',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LearningLanguageSerailizer,
            },
        },
        'learning_language_destroy': {
            'summary': 'Удаление языка из изучаемых',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: LearningLanguageWithLastWordsSerailizer,
            },
        },
        'language_collections_list': {
            'summary': 'Просмотр всех коллекций изучаемого языка',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LearningLanguageSerailizer,
            },
        },
        'native_languages_list': {
            'summary': 'Просмотр всех родных языков пользователя',
            'request': None,
            'responses': {
                status.HTTP_200_OK: NativeLanguageSerailizer,
            },
        },
        'native_language_create': {
            'summary': 'Добавление родного языка',
            'request': NativeLanguageSerailizer,
            'responses': {
                status.HTTP_201_CREATED: NativeLanguageSerailizer(many=True),
            },
        },
        'all_languages_list': {
            'summary': 'Просмотр списка всех языков',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageSerailizer,
            },
        },
        'languages_available_for_learning_list': {
            'summary': 'Просмотр всех языков доступных для изучения',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageSerailizer,
            },
        },
        'learning_and_available_languages_list': {
            'summary': 'Просмотр текущих изучаемых языков и языков доступных для изучения',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LearningLanguageShortSerailizer,
            },
        },
        'interface_switch_languages_list': {
            'summary': 'Просмотр всех языков доступных для перевода интерфейса',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageSerailizer,
            },
        },
        'language_images_choice_retrieve': {
            'summary': 'Просмотр всех доступных картинок для изучаемого языка',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ImageShortSerailizer,
            },
        },
        'language_image_update': {
            'summary': 'Обновление выбранной картинки для изучаемого языка',
            'request': ImageShortSerailizer,
            'responses': {
                status.HTTP_201_CREATED: LearningLanguageSerailizer,
            },
        },
        # other methods
    },
    'ExerciseViewSet': {
        'tags': ['exercises'],
        'exercises_list': {
            'summary': 'Просмотр библиотеки упражнений',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ExerciseListSerializer,
            },
        },
        'exercise_retrieve': {
            'summary': 'Просмотр профиля упражнения',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ExerciseProfileSerializer,
            },
        },
        'exercises_list_for_anonymous': {
            'summary': 'Просмотр библиотеки упражнений (для неавторизованных)',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ExerciseListSerializer,
            },
        },
        'exercise_sets_list': {
            'summary': 'Просмотр списка наборов слов для этого упражнения',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SetListSerializer,
            },
        },
        'exercise_sets_create': {
            'summary': 'Создание набора слов для этого упражнения',
            'request': SetSerializer,
            'responses': {
                status.HTTP_201_CREATED: SetSerializer,
            },
        },
        'exercise_set_retrieve': {
            'summary': 'Просмотр набора слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SetSerializer,
            },
        },
        'exercise_set_partial_update': {
            'summary': 'Редактирование набора слов',
            'request': SetSerializer,
            'responses': {
                status.HTTP_200_OK: SetSerializer,
            },
        },
        'exercise_set_destroy': {
            'summary': 'Удаление набора слов для этого упражнения',
            'request': None,
            'responses': {
                status.HTTP_204_NO_CONTENT: SetListSerializer,
            },
        },
        'exercise_last_approach_retrieve': {
            'summary': 'Просмотр последнего подхода в этом упражнении',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LastApproachProfileSerializer,
            },
        },
        'exercise_available_words_retrieve': {
            'summary': 'Просмотр доступных для этого упражнения слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordStandartCardSerializer,
            },
        },
        'exercise_available_collections_retrieve': {
            'summary': 'Просмотр доступных для этого упражнения коллекций',
            'request': None,
            'responses': {
                status.HTTP_200_OK: CollectionWithAvailableWordsSerializer,
            },
        },
        'translator_default_settings_retrieve': {
            'summary': 'Просмотр дефолтных настроек пользователя для упражнения `Переводчик`',
            'request': None,
            'responses': {
                status.HTTP_200_OK: TranslatorUserDefaultSettingsSerializer,
            },
        },
        'translator_default_settings_partial_update': {
            'summary': 'Обновление дефолтных настроек пользователя для упражнения `Переводчик`',
            'request': TranslatorUserDefaultSettingsSerializer,
            'responses': {
                status.HTTP_200_OK: TranslatorUserDefaultSettingsSerializer,
            },
        },
        'exercises_favorites_list': {
            'summary': 'Просмотр списка избранных упражнений',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ExerciseListSerializer,
            },
        },
        'exercise_favorite_create': {
            'summary': 'Добавление упражнения в список избранных',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ExerciseListSerializer,
            },
        },
        'exercise_favorite_destroy': {
            'summary': 'Удаление упражнения из списка избранных',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ExerciseListSerializer,
            },
        },
        # other methods
    },
    'UserViewSet': {
        'tags': ['users'],
        'users_list': {
            'summary': 'Просмотр списка пользователей',
            'request': None,
            'responses': {
                status.HTTP_200_OK: UserShortSerializer,
            },
        },
        # other methods
    },
    # other viewsets
}
