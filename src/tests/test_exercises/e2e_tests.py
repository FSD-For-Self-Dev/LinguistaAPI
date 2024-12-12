import json
import pytest
import logging
from model_bakery import baker

from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.vocabulary.models import Word, WordTranslation, Collection
from apps.exercises.models import FavoriteExercise, TranslatorUserDefaultSettings

logger = logging.getLogger(__name__)

User = get_user_model()

pytestmark = [pytest.mark.django_db, pytest.mark.e2e]


def get_yesterday_date():
    return timezone.localdate() - timezone.timedelta(days=1)


@pytest.mark.exercises
class TestExercisesEndpoints:
    endpoint = '/api/exercises/'

    @pytest.mark.parametrize(
        'pagination_field',
        [
            ('count'),
            ('next'),
            ('previous'),
            ('results'),
        ],
    )
    def test_list(self, auth_api_client, user, pagination_field, exercises):
        exercises(extra_data={'available': True})
        exercises(extra_data={'available': False})

        response = auth_api_client(user).get(self.endpoint)
        if response.status_code == 307:
            response = auth_api_client(user).get(response['Location'])

        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert pagination_field in response.data, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются данные с пагинацией. '
            f'Не найден параметр `{pagination_field}`'
        )
        assert response_content['count'] == 1
        assert len(response_content['unavailable']) == 1

    def test_retrieve(self, auth_api_client, user, exercises):
        exercise = exercises(extra_data={'available': True})[0]

        response = auth_api_client(user).get(f'{self.endpoint}{exercise.slug}/')
        if response.status_code == 307:
            response = auth_api_client(user).get(response['Location'])

        assert response.status_code == 200

    def test_list_for_anonymous(self, api_client, exercises):
        exercises(extra_data={'available': True})
        exercises(extra_data={'available': False})

        response = api_client().get(f'{self.endpoint}anonymous/')
        if response.status_code == 307:
            response = api_client().get(response['Location'])

        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert response_content['count'] == 2

    # def test_random_exercises_action(self, auth_api_client, user):
    #     baker.make(Word, author=user, _quantity=3)

    #     response = auth_api_client(user).get(
    #         f'{self.endpoint}random/'
    #     )

    #     assert response.status_code == 200

    def test_retrieve_available_words(self, auth_api_client, user, exercises):
        exercise = exercises(
            extra_data={'available': True, 'name': 'translator', 'slug': 'translator'}
        )[0]
        word = baker.make(Word, author=user)
        translation = baker.make(WordTranslation, author=user, _fill_optional=True)
        word.translations.add(translation)

        response = auth_api_client(user).get(
            f'{self.endpoint}{exercise.slug}/available-words/'
        )
        if response.status_code == 307:
            response = auth_api_client(user).get(response['Location'])

        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert response_content['words']['count'] == 1

    def test_retrieve_available_collections(self, auth_api_client, user, exercises):
        exercise = exercises(
            extra_data={'available': True, 'name': 'translator', 'slug': 'translator'}
        )[0]
        word = baker.make(Word, author=user)
        translation = baker.make(WordTranslation, author=user, _fill_optional=True)
        word.translations.add(translation)
        other_word = baker.make(Word, author=user)
        right_collection = baker.make(Collection, author=user)
        right_collection.words.add(word)
        semi_right_collection = baker.make(Collection, author=user)
        semi_right_collection.words.add(word, other_word)
        baker.make(Collection, author=user)

        response = auth_api_client(user).get(
            f'{self.endpoint}{exercise.slug}/available-collections/'
        )
        if response.status_code == 307:
            response = auth_api_client(user).get(response['Location'])

        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert response_content['collections']['count'] == 2

    def test_retrieve_last_approach(
        self, auth_api_client, user, exercises, exercise_history
    ):
        exercise = exercises(extra_data={'available': True})[0]
        approach = exercise_history(extra_data={'user': user})
        exercise.users_history.set(approach)

        response = auth_api_client(user).get(
            f'{self.endpoint}{exercise.slug}/last-approach/'
        )
        if response.status_code == 307:
            response = auth_api_client(user).get(response['Location'])

        assert response.status_code == 200

    def test_set_list(self, auth_api_client, user, exercises, word_sets):
        exercise = exercises(extra_data={'available': True})[0]
        word_sets(extra_data={'author': user, 'exercise': exercise})

        response = auth_api_client(user).get(
            f'{self.endpoint}{exercise.slug}/word-sets/'
        )
        if response.status_code == 307:
            response = auth_api_client(user).get(response['Location'])

        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert response_content['count'] == 1

    def test_set_create(self, auth_api_client, user, exercises, word_sets):
        exercise = exercises(extra_data={'available': True})[0]
        word_set, source_data, _ = word_sets(
            extra_data={'author': user, 'exercise': exercise},
            data=True,
            make=False,
        )

        response = auth_api_client(user).post(
            f'{self.endpoint}{exercise.slug}/word-sets/',
            data=source_data,
            format='json',
        )
        if response.status_code == 307:
            response = auth_api_client(user).post(
                response['Location'],
                data=source_data,
                format='json',
            )

        assert response.status_code == 201

    def test_set_retrieve(self, auth_api_client, user, exercises, word_sets):
        exercise = exercises(extra_data={'available': True})[0]
        word_set = word_sets(extra_data={'author': user, 'exercise': exercise})[0]

        response = auth_api_client(user).get(
            f'{self.endpoint}{exercise.slug}/word-sets/{word_set.slug}/'
        )
        if response.status_code == 307:
            response = auth_api_client(user).get(response['Location'])

        assert response.status_code == 200

    def test_set_partial_update(self, auth_api_client, user, exercises, word_sets):
        exercise = exercises(extra_data={'available': True})[0]
        word_set = word_sets(
            extra_data={'author': user, 'exercise': exercise},
            data=False,
            make=True,
        )[0]
        _, source_data, _ = word_sets(
            extra_data={'author': user, 'exercise': exercise},
            data=True,
            make=False,
        )

        response = auth_api_client(user).patch(
            f'{self.endpoint}{exercise.slug}/word-sets/{word_set.slug}/',
            data=source_data[0],
            format='json',
        )
        if response.status_code == 307:
            response = auth_api_client(user).patch(
                response['Location'],
                data=source_data[0],
                format='json',
            )

        assert response.status_code == 200

    def test_set_destroy(self, auth_api_client, user, exercises, word_sets):
        exercise = exercises(extra_data={'available': True})[0]
        word_set = word_sets(extra_data={'author': user, 'exercise': exercise})[0]

        response = auth_api_client(user).delete(
            f'{self.endpoint}{exercise.slug}/word-sets/{word_set.slug}/'
        )
        if response.status_code == 307:
            response = auth_api_client(user).delete(response['Location'])

        assert response.status_code in (204, 200)

    def test_default_settings_retrieve(self, auth_api_client, user):
        TranslatorUserDefaultSettings.objects.get_or_create(user=user)

        response = auth_api_client(user).get(
            f'{self.endpoint}translator-default-settings/',
        )
        if response.status_code == 307:
            response = auth_api_client(user).get(response['Location'])

        assert response.status_code == 200

    def test_default_settings_partial_update(self, auth_api_client, user, exercises):
        exercise_default_settings = baker.prepare(
            TranslatorUserDefaultSettings,
            user=user,
            answer_time_limit='00:00:30',
            repetitions_amount=5,
            _fill_optional=True,
        )
        source_data = {
            'mode': exercise_default_settings.mode,
            'answer_time_limit': exercise_default_settings.answer_time_limit,
            'repetitions_amount': exercise_default_settings.repetitions_amount,
            'from_language': exercise_default_settings.from_language,
        }

        response = auth_api_client(user).patch(
            f'{self.endpoint}translator-default-settings/',
            data=source_data,
            format='json',
        )
        if response.status_code == 307:
            response = auth_api_client(user).patch(
                response['Location'],
                data=source_data,
                format='json',
            )

        assert response.status_code == 200

    def test_word_favorites_list_action(self, auth_api_client, user, exercises):
        exercise = exercises()[0]
        FavoriteExercise.objects.create(user=user, exercise=exercise)

        response = auth_api_client(user).get(f'{self.endpoint}favorites/')
        if response.status_code == 307:
            response = auth_api_client(user).get(response['Location'])

        assert response.data['count'] == 1

    def test_word_favorite_create_action(self, auth_api_client, user, exercises):
        exercise = exercises()[0]

        response = auth_api_client(user).post(
            f'{self.endpoint}{exercise.slug}/favorite/'
        )
        if response.status_code == 307:
            response = auth_api_client(user).post(response['Location'])

        assert FavoriteExercise.objects.filter(user=user, exercise=exercise).exists()

    def test_word_favorite_destroy_action(self, auth_api_client, user, exercises):
        exercise = exercises()[0]

        response = auth_api_client(user).delete(
            f'{self.endpoint}{exercise.slug}/favorite/'
        )
        if response.status_code == 307:
            response = auth_api_client(user).delete(response['Location'])

        assert not FavoriteExercise.objects.filter(
            user=user, exercise=exercise
        ).exists()
