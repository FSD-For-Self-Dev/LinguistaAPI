"""Exercises schema data."""

from rest_framework import status

from api.v1.vocabulary.serializers import (
    WordStandartCardSerializer,
)
from api.v1.exercises.serializers import (
    ExerciseListSerializer,
    ExerciseProfileSerializer,
    SetListSerializer,
    SetSerializer,
    LastApproachProfileSerializer,
    CollectionWithAvailableWordsSerializer,
    TranslatorUserDefaultSettingsSerializer,
)


data = {
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
}
