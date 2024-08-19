"""Custom schema generator."""

import os
import logging

from rest_framework import status
from rest_framework.serializers import (
    Serializer,
    CharField,
    IntegerField,
    ListField,
)
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    OpenApiResponse,
    OpenApiExample,
    inline_serializer,
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
    LanguageImageSerailizer,
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
    NoteInLineSerializer,
    NoteForWordSerializer,
    SynonymForWordListSerializer,
    SynonymInLineSerializer,
    AntonymForWordListSerializer,
    AntonymInLineSerializer,
    FormForWordListSerializer,
    FormInLineSerializer,
    SimilarForWordListSerializer,
    SimilarInLineSerializer,
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
from users.constants import UsersAmountLimits
from languages.serializers import LanguageSerializer

from .exceptions import ExceptionCodes, ExceptionDetails

logger = logging.getLogger(__name__)


class CustomSchema(AutoSchema):
    """Custom schema generator to generate schema from common data dictionary."""

    def get_tags(self) -> list[str]:
        try:
            return data[self.view.__class__.__name__]['tags']
        except Exception:
            return data['default']['tags']

    def get_description(self) -> str | None:
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'description'
            ]
        except Exception:
            return super().get_description()

    def get_summary(self) -> str | None:
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'summary'
            ]
        except Exception:
            logger.warning(
                f'Информация об операции отсутствует в данных схемы (не передан `summary`) '
                f'[{self.view.__class__.__name__}: {self.get_operation_id().lower()}]'
            )
            return super().get_summary()

    def get_request_serializer(self) -> Serializer | None:
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'request'
            ]
        except Exception:
            return super().get_request_serializer()

    def get_response_serializers(self) -> dict[int, OpenApiResponse]:
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'responses'
            ]
        except Exception:
            return super().get_response_serializers()

    def get_examples(self):
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'examples'
            ]
        except Exception:
            return super().get_examples()

    def get_override_parameters(self) -> list[OpenApiParameter]:
        try:
            return data[self.view.__class__.__name__][self.get_operation_id().lower()][
                'parameters'
            ]
        except Exception:
            return super().get_override_parameters()


data = {
    'default': {
        'tags': ['default'],
    },
    'Fixed': {
        'tags': ['authentication'],
        os.getenv('LOGIN_URL_REVERSE_NAME', default='api_auth_login_create'): {
            'summary': 'Вход в аккаунт',
            'request': inline_serializer(
                name='InlineLoginSerializer',
                fields={
                    'username': CharField(),
                    'password': CharField(),
                },
            ),
        },
        os.getenv('LOGOUT_URL_REVERSE_NAME', default='api_auth_logout_create'): {
            'summary': 'Выход из аккаунта',
        },
        os.getenv(
            'PASSWORD_CHANGE_URL_REVERSE_NAME',
            default='api_auth_password_change_create',
        ): {
            'summary': 'Изменение пароля',
        },
        os.getenv(
            'PASSWORD_RESET_URL_REVERSE_NAME', default='api_auth_password_reset_create'
        ): {
            'summary': 'Восстановление пароля',
        },
        os.getenv(
            'PASSWORD_RESET_CONFIRM_URL_REVERSE_NAME',
            default='api_auth_password_reset_confirm_create',
        ): {
            'summary': 'Подтверждение восстановления пароля',
        },
        os.getenv(
            'REGISTRATION_URL_REVERSE_NAME', default='api_auth_registration_create'
        ): {
            'summary': 'Регистрация',
        },
        os.getenv(
            'REGISTRATION_RESEND_EMAIL_URL_REVERSE_NAME',
            default='api_auth_registration_resend_email_create',
        ): {
            'summary': 'Повторная отправка сообщения с подтверждением e-mail адреса',
        },
        os.getenv(
            'REGISTRATION_VERIFY_EMAIL_URL_REVERSE_NAME',
            default='api_auth_registration_verify_email_create',
        ): {
            'summary': 'Подтверждение e-mail адреса',
            'description': (
                'Передайте в теле запроса ключ подтверждения, чтобы подтвердить '
                'свой e-mail адрес. '
                'Возвращает сообщение об успехе/ошибке.'
            ),
        },
        # other methods
    },
    'UserDetailsWithDestroyView': {
        'tags': ['user_profile'],
        'user_retrieve': {
            'summary': 'Просмотр профиля пользователя',
        },
        'user_update': {
            'summary': 'Редактирование профиля пользователя',
        },
        'user_partial_update': {
            'summary': 'Редактирование профиля пользователя',
        },
        'user_destroy': {
            'summary': 'Удаление аккаунта пользователя',
        },
        # other methods
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
                status.HTTP_200_OK: WordStandartCardSerializer,
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
                status.HTTP_200_OK: WordTranslationInLineSerializer,
            },
        },
        'word_translation_partial_update': {
            'summary': 'Редактирование перевода слова',
            'request': WordTranslationInLineSerializer,
            'responses': {
                status.HTTP_200_OK: WordTranslationInLineSerializer,
            },
        },
        'word_translation_destroy': {
            'summary': 'Удаление перевода слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: WordTranslationInLineSerializer,
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
                status.HTTP_200_OK: DefinitionInLineSerializer,
            },
        },
        'word_definition_partial_update': {
            'summary': 'Редактирование определения слова',
            'request': DefinitionInLineSerializer,
            'responses': {
                status.HTTP_200_OK: DefinitionInLineSerializer,
            },
        },
        'word_definition_destroy': {
            'summary': 'Удаление определения слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: DefinitionInLineSerializer,
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
                status.HTTP_200_OK: UsageExampleInLineSerializer,
            },
        },
        'word_example_partial_update': {
            'summary': 'Редактирование примера использования слова',
            'request': UsageExampleInLineSerializer,
            'responses': {
                status.HTTP_200_OK: UsageExampleInLineSerializer,
            },
        },
        'word_example_destroy': {
            'summary': 'Удаление примера использования слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: UsageExampleInLineSerializer,
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
                status.HTTP_200_OK: WordSerializer,
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
                status.HTTP_200_OK: SynonymInLineSerializer,
            },
        },
        'word_synonym_partial_update': {
            'summary': 'Редактирование синонима слова',
            'request': SynonymInLineSerializer,
            'responses': {
                status.HTTP_200_OK: SynonymInLineSerializer,
            },
        },
        'word_synonym_destroy': {
            'summary': 'Удаление синонима слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SynonymForWordListSerializer,
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
                status.HTTP_200_OK: AntonymInLineSerializer,
            },
        },
        'word_antonym_partial_update': {
            'summary': 'Редактирование антонима слова',
            'request': AntonymInLineSerializer,
            'responses': {
                status.HTTP_200_OK: AntonymInLineSerializer,
            },
        },
        'word_antonym_destroy': {
            'summary': 'Удаление антонима слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: AntonymForWordListSerializer,
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
                status.HTTP_200_OK: FormInLineSerializer,
            },
        },
        'word_form_partial_update': {
            'summary': 'Редактирование формы слова',
            'request': FormInLineSerializer,
            'responses': {
                status.HTTP_200_OK: FormInLineSerializer,
            },
        },
        'word_form_destroy': {
            'summary': 'Удаление формы слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: FormForWordListSerializer,
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
                status.HTTP_200_OK: SimilarInLineSerializer,
            },
        },
        'word_similar_partial_update': {
            'summary': 'Редактирование похожего слова слова',
            'request': SimilarInLineSerializer,
            'responses': {
                status.HTTP_200_OK: SimilarInLineSerializer,
            },
        },
        'word_similar_destroy': {
            'summary': 'Удаление похожего слова слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SimilarForWordListSerializer,
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
        'word_images_list': {
            'summary': 'Просмотр списка всех картинок-ассоциаций слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ImageInLineSerializer,
            },
        },
        'word_image_retrieve': {
            'summary': 'Просмотр картинки-ассоциации слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ImageInLineSerializer,
            },
        },
        'word_image_partial_update': {
            'summary': 'Редактирование картинки-ассоциации слова',
            'request': ImageInLineSerializer,
            'responses': {
                status.HTTP_200_OK: ImageInLineSerializer,
            },
        },
        'word_image_destroy': {
            'summary': 'Удаление картинки-ассоциации слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: ImageInLineSerializer,
            },
        },
        'word_quotes_list': {
            'summary': 'Просмотр списка всех цитат-ассоциаций слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: QuoteInLineSerializer,
            },
        },
        'word_quote_retrieve': {
            'summary': 'Просмотр цитаты-ассоциации слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: QuoteInLineSerializer,
            },
        },
        'word_quote_partial_update': {
            'summary': 'Редактирование цитаты-ассоциации слова',
            'request': QuoteInLineSerializer,
            'responses': {
                status.HTTP_200_OK: QuoteInLineSerializer,
            },
        },
        'word_quote_destroy': {
            'summary': 'Удаление цитаты-ассоциации слова',
            'request': None,
            'responses': {
                status.HTTP_200_OK: QuoteInLineSerializer,
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
                status.HTTP_200_OK: WordSerializer,
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
                status.HTTP_200_OK: CollectionShortSerializer,
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
    'LanguageViewSet': {
        'tags': ['learning_languages'],
        'learning_languages_list': {
            'summary': 'Просмотр списка изучаемых языков пользователя',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LearningLanguageWithLastWordsSerailizer(many=True),
            },
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
                        name='learning_languages_list',
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
                        name='exception_details',
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
                                'detail': ExceptionDetails.Users.LEARNING_LANGUAGE_ALREADY_EXIST,
                                'existing_object': 'English',
                            },
                        ),
                        OpenApiExample(
                            name=ExceptionCodes.AMOUNT_LIMIT_EXCEEDED,
                            value={
                                'exception_code': ExceptionCodes.AMOUNT_LIMIT_EXCEEDED,
                                'detail': UsersAmountLimits.Details.LEARNING_LANGUAGES_AMOUNT_EXCEEDED,
                                'amount_limit': UsersAmountLimits.MAX_LEARNING_LANGUAGES_AMOUNT,
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
                        name='exception_details',
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
                                        ExceptionDetails.Users.LANGUAGE_NOT_AVAILABLE
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
                status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                    description=(
                        'Пользователь не авторизован.\n'
                        'Не был передан заголовок Authorization.',
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
                ),
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
                status.HTTP_204_NO_CONTENT: None,
            },
        },
        'language_collections_list': {
            'summary': 'Просмотр всех коллекций изучаемого языка',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LearningLanguageSerailizer(many=True),
            },
        },
        'native_languages_list': {
            'summary': 'Просмотр всех родных языков пользователя',
            'request': None,
            'responses': {
                status.HTTP_200_OK: NativeLanguageSerailizer(many=True),
            },
        },
        'native_language_create': {
            'summary': 'Добавление родных языков',
            'request': NativeLanguageSerailizer(many=True),
            'responses': {
                status.HTTP_201_CREATED: NativeLanguageSerailizer(many=True),
            },
        },
        'all_languages_list': {
            'summary': 'Просмотр списка всех языков',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageSerializer(many=True),
            },
        },
        'languages_available_for_learning_list': {
            'summary': 'Просмотр всех языков доступных для изучения',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageSerializer(many=True),
            },
        },
        'interface_switch_languages_list': {
            'summary': 'Просмотр всех языков доступных для перевода интерфейса',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageSerializer(many=True),
            },
        },
        'language_cover_choices_retrieve': {
            'summary': 'Просмотр всех доступных картинок для изучаемого языка',
            'request': None,
            'responses': {
                status.HTTP_200_OK: LanguageImageSerailizer(many=True),
            },
        },
        'language_cover_set': {
            'summary': 'Обновление выбранной картинки для изучаемого языка',
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
        'exercise_words_sets_list': {
            'summary': 'Просмотр списка наборов слов для этого упражнения',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SetListSerializer,
            },
        },
        'exercise_words_sets_create': {
            'summary': 'Создание набора слов для этого упражнения',
            'request': SetSerializer,
            'responses': {
                status.HTTP_201_CREATED: SetSerializer,
            },
        },
        'exercise_words_set_retrieve': {
            'summary': 'Просмотр набора слов',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SetSerializer,
            },
        },
        'exercise_words_set_partial_update': {
            'summary': 'Редактирование набора слов',
            'request': SetSerializer,
            'responses': {
                status.HTTP_200_OK: SetSerializer,
            },
        },
        'exercise_words_set_destroy': {
            'summary': 'Удаление набора слов для этого упражнения',
            'request': None,
            'responses': {
                status.HTTP_200_OK: SetListSerializer,
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
