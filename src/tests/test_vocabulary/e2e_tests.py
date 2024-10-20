from model_bakery import baker
import json
import pytest
import logging

from django.utils import timezone
from django.db.models import Max, Min, Count
from django.contrib.auth import get_user_model

from apps.vocabulary.models import (
    Word,
    WordTag,
    WordType,
    WordTranslation,
    UsageExample,
    Definition,
    FavoriteWord,
    Collection,
    FavoriteCollection,
    FormGroup,
    WordsInCollections,
    ImageAssociation,
    QuoteAssociation,
)
from apps.languages.models import Language, UserLearningLanguage
from apps.core.constants import AmountLimits

logger = logging.getLogger(__name__)

User = get_user_model()

pytestmark = [pytest.mark.django_db, pytest.mark.e2e]


def get_yesterday_date():
    return timezone.localdate() - timezone.timedelta(days=1)


@pytest.mark.vocabulary
class TestVocabularyEndpoints:
    endpoint = '/api/vocabulary/'

    @pytest.mark.parametrize(
        'pagination_field',
        [
            ('count'),
            ('next'),
            ('previous'),
            ('results'),
        ],
    )
    def test_list(self, auth_api_client, user, pagination_field):
        """
        По запросу словаря возвращается список слов из словаря авторизованного
        пользователя с пагинацией.
        """
        user_words = baker.make(Word, author=user, _quantity=3)
        other_user = baker.make(User)
        baker.make(Word, author=other_user)

        response = auth_api_client(user).get(self.endpoint)

        assert response.status_code == 200
        assert pagination_field in response.data, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются данные с пагинацией. '
            f'Не найден параметр `{pagination_field}`'
        )
        assert response.data['count'] == len(user_words), (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == len(user_words)

    def test_list_not_auth(self, api_client):
        """
        На запрос получения словаря от неавторизованного пользователя
        возвращается ошибка 401.
        """
        response = api_client().get(self.endpoint)

        assert response.status_code == 401

    @pytest.mark.parametrize(
        'order_field, reverse_ordering, format',
        [
            ('text', False, None),
            ('text', True, None),
            ('created', False, '%Y-%m-%d %H:%M'),
            ('created', True, '%Y-%m-%d %H:%M'),
            ('last_exercise_date', False, '%Y-%m-%d %H:%M'),
            ('last_exercise_date', True, '%Y-%m-%d %H:%M'),
        ],
    )
    def test_ordering_by_word_attr(
        self, auth_api_client, user, order_field, reverse_ordering, format
    ):
        """Сортировка слов работает по тексту, по дате добавления,
        дате последней тренировки (по возрастанию и убыванию)."""
        baker.make(Word, author=user, _quantity=10, _fill_optional=[order_field])
        query = ('-' if reverse_ordering else '') + order_field
        (first_value,) = Word.objects.aggregate(Min(order_field)).values()
        (last_value,) = Word.objects.aggregate(Max(order_field)).values()
        if reverse_ordering:
            first_value, last_value = last_value, first_value
        if format:
            first_value = first_value.strftime('%Y-%m-%d %H:%M')
            last_value = last_value.strftime('%Y-%m-%d %H:%M')

        response = auth_api_client(user).get(
            self.endpoint,
            {'ordering': query},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['results'][0][order_field] == first_value
        assert response.data['results'][-1][order_field] == last_value

    @pytest.mark.parametrize(
        'order_field, reverse_ordering, objs_related_name',
        [
            ('translations_count', False, 'translations'),
            ('translations_count', True, 'translations'),
        ],
    )
    def test_ordering_by_related_objs_count(
        self, auth_api_client, user, order_field, reverse_ordering, objs_related_name
    ):
        """
        Сортировка словаря работает по дате создания, кол-ву переводов
        (по возрастанию и убыванию).
        """
        baker.make(Word, author=user, _quantity=10)
        query = ('-' if reverse_ordering else '') + order_field
        (first_value,) = (
            Word.objects.annotate(
                **{order_field: Count(objs_related_name, distinct=True)}
            )
            .aggregate(Max(order_field))
            .values()
        )
        (last_value,) = (
            Word.objects.annotate(
                **{order_field: Count(objs_related_name, distinct=True)}
            )
            .aggregate(Min(order_field))
            .values()
        )
        if reverse_ordering:
            first_value, last_value = last_value, first_value

        response = auth_api_client(user).get(
            self.endpoint,
            {'ordering': query},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['results'][0][order_field] == first_value
        assert response.data['results'][-1][order_field] == last_value

    @pytest.mark.parametrize('search_attr', ['text'])
    def test_search_by_word_attr(self, auth_api_client, user, search_attr):
        """Поиск по словам работает по тексту слов."""
        word = baker.make(Word, author=user)
        baker.make(Word, author=user, _quantity=10)

        response = auth_api_client(user).get(
            self.endpoint,
            {'search': word.__getattribute__(search_attr)},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['count'] == 1, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == 1

    @pytest.mark.parametrize(
        'search_field, search_attr, related_model',
        [
            ('translations', 'text', WordTranslation),
            ('tags', 'name', WordTag),
            ('definitions', 'text', Definition),
            ('definitions', 'translation', Definition),
        ],
    )
    def test_search_by_related_attr(
        self, auth_api_client, user, search_field, search_attr, related_model
    ):
        """
        Поиск по словам работает по тексту переводов, тексту определений,
        переводу определений, названию тегов.
        """
        word = baker.make(Word, author=user)
        baker.make(Word, author=user, _quantity=10)
        obj = baker.make(related_model, _fill_optional=[search_attr])
        word.__getattribute__(search_field).add(obj)

        response = auth_api_client(user).get(
            self.endpoint,
            {'search': obj.__getattribute__(search_attr)},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['count'] == 1, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == 1

    @pytest.mark.parametrize(
        'filter_field, related_model',
        [
            ('translations', WordTranslation),
            ('examples', UsageExample),
        ],
    )
    def test_filter_by_objs_count(
        self, auth_api_client, user, filter_field, related_model
    ):
        """Фильтрация слов работает по кол-ву переводов, примеров."""
        obj = baker.make(related_model)
        word = baker.make(Word, author=user)
        word.__getattribute__(filter_field).add(obj)
        baker.make(Word, author=user, _quantity=10)
        query_field = filter_field + '_count'

        response = auth_api_client(user).get(
            self.endpoint,
            {query_field: 1},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['count'] == 1, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == 1

    @pytest.mark.parametrize(
        'filter_field, filter_value, lookup',
        [
            ('activity_status', 'A', None),
            ('is_problematic', True, None),
            ('created', get_yesterday_date(), 'date'),
            ('last_exercise_date', get_yesterday_date(), 'date'),
        ],
    )
    def test_filter_by_word_attr(
        self, auth_api_client, user, filter_field, filter_value, lookup
    ):
        """
        Фильтрация слов работает по статусу активности, тегу проблемное,
        дате добавления, дате последней тренировки с этим словом.
        """
        baker.make(Word, author=user, **{filter_field: filter_value})
        baker.make(Word, author=user, _quantity=10)
        query_field = filter_field + '__' + lookup if lookup else filter_field

        response = auth_api_client(user).get(
            self.endpoint,
            {query_field: filter_value},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['count'] == 1, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == 1

    @pytest.mark.parametrize(
        'filter_field, related_model, filter_attr, use_manager',
        [
            ('tags', WordTag, 'name', True),
            ('types', WordType, 'slug', True),
            ('language', Language, 'isocode', False),
        ],
    )
    def test_filter_by_related_objs(
        self,
        auth_api_client,
        user,
        filter_field,
        related_model,
        filter_attr,
        use_manager,
    ):
        """
        Фильтрация слов работает по названию тегов, слагу типов, коду языков.
        """
        obj = baker.make(related_model)
        if use_manager:
            word = baker.make(Word, author=user)
            word.__getattribute__(filter_field).add(obj)
        else:
            word = baker.make(Word, author=user, **{filter_field: obj})
        baker.make(Word, author=user, _quantity=10)

        response = auth_api_client(user).get(
            self.endpoint,
            {filter_field: obj.__getattribute__(filter_attr)},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['count'] == 1, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == 1

    @pytest.mark.parametrize(
        'filter_field, fixture_name, filter_attr',
        [
            ('tags', 'word_tags', 'name'),
            ('types', 'word_types', 'slug'),
        ],
    )
    def test_filter_values_list(
        self, auth_api_client, user, filter_field, fixture_name, filter_attr, request
    ):
        """Фильтрация слов работает по нескольким тегам, типам."""
        fixture = request.getfixturevalue(fixture_name)
        obj1 = fixture(user, make=True)
        obj2 = fixture(user, make=True)
        word1 = baker.make(Word, author=user)
        word1.__getattribute__(filter_field).set(obj1)
        word2 = baker.make(Word, author=user)
        word2.__getattribute__(filter_field).set(obj2)
        baker.make(Word, author=user, _quantity=10)
        filter_value1 = obj1[0].__getattribute__(filter_attr)
        filter_value2 = obj2[0].__getattribute__(filter_attr)

        response = auth_api_client(user).get(
            self.endpoint,
            {filter_field: filter_value1 + ',' + filter_value2},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['count'] == 2, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == 2

    def test_filter_by_first_letter(self, auth_api_client, user):
        """Фильтрация слов работает по первой букве слова."""
        baker.make(Word, author=user, text='test word')
        baker.make(Word, author=user, text='word test')

        response = auth_api_client(user).get(
            self.endpoint,
            {'first_letter': 't'},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['count'] == 1, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == 1

    @pytest.mark.parametrize(
        'related_model, related_manager',
        [
            (ImageAssociation, 'image_associations'),
            (QuoteAssociation, 'quote_associations'),
        ],
    )
    def test_filter_by_have_associations(
        self, auth_api_client, user, related_model, related_manager
    ):
        """Фильтрация слов работает по наличию ассоциаций."""
        association = baker.make(related_model, author=user)
        word = baker.make(Word, author=user)
        word.__getattribute__(related_manager).add(association)
        baker.make(Word, author=user, _quantity=10)

        response = auth_api_client(user).get(
            self.endpoint, {'have_associations': True}, format='json'
        )

        assert response.status_code == 200
        assert response.data['count'] == 1, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == 1

    def test_word_create_simple_data(self, auth_api_client, user, learning_language):
        """
        Слово успешно создается при запросе с валидными данными от авторизованного
        пользователя.
        """
        language = learning_language(user)
        word = baker.prepare(Word, author=user, language=language, _fill_optional=True)
        word_types = baker.make(WordType, _quantity=1)
        word_tags = baker.prepare(WordTag, _quantity=1)
        source_json = {
            'language': word.language.name,
            'text': word.text,
            'is_problematic': word.is_problematic,
            'note': word.note,
            'favorite': True,
            'types': [word_type.name for word_type in word_types],
            'tags': [{'name': word_tag.name.lower()} for word_tag in word_tags],
        }
        expected_data = {
            'language': word.language.name,
            'text': word.text,
            'is_problematic': word.is_problematic,
            'note': word.note,
            'favorite': True,
            'types': [word_type.name for word_type in word_types],
            'tags': [{'name': word_tag.name.lower()} for word_tag in word_tags],
        }

        response = auth_api_client(user).post(
            self.endpoint, data=source_json, format='json'
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert all(
            [response_content[field] == value for field, value in expected_data.items()]
        )

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name, counter, res_name',
        [
            ('form_groups', 'word_form_groups', False, 'form_groups'),
            ('translations', 'word_translations', True, 'translations'),
            ('examples', 'word_usage_examples', True, 'examples'),
            ('definitions', 'word_definitions', True, 'definitions'),
            ('collections', 'collections', True, 'collections'),
            # ('image_associations', 'word_image_associations', True, 'associations'),
            ('quote_associations', 'word_quote_associations', True, 'associations'),
        ],
    )
    def test_word_create_with_related_objs(
        self,
        auth_api_client,
        user,
        learning_language,
        objs_related_name,
        fixture_name,
        counter,
        res_name,
        request,
    ):
        """
        Слово успешно создается вместе со связанными объектами
        при запросе с валидными данными от авторизованного пользователя.
        """
        language = learning_language(user)
        word = baker.prepare(Word, author=user, language=language)
        (
            _,
            related_objs_source_data,
            related_objs_expected_data,
        ) = request.getfixturevalue(fixture_name)(user, data=True, language=language)
        source_json = {
            'language': word.language.name,
            'text': word.text,
            objs_related_name: related_objs_source_data,
        }

        response = auth_api_client(user).post(
            self.endpoint, data=source_json, format='json'
        )
        response_objs_content = json.loads(response.content)[res_name]

        assert response.status_code == 201
        assert len(response_objs_content) == len(related_objs_expected_data)
        assert all(
            [
                response_objs_content[0][field] == value
                for field, value in related_objs_expected_data[0].items()
            ]
        )
        if counter:
            assert json.loads(response.content)[res_name + '_count'] == len(
                related_objs_expected_data
            )

    @pytest.mark.parametrize(
        'objs_related_name, note',
        [
            ('synonyms', 'test note'),
            ('antonyms', 'test note'),
            ('forms', None),
            ('similars', None),
        ],
    )
    def test_word_create_with_related_words(
        self, auth_api_client, user, learning_language, objs_related_name, note, request
    ):
        """
        Слово успешно создается вместе со связанными словами
        при запросе с валидными данными от авторизованного пользователя.
        """
        language = learning_language(user)
        word = baker.prepare(Word, author=user, language=language)
        (
            _,
            related_words_source_data,
            related_words_expected_data,
        ) = request.getfixturevalue('related_words_data')(
            user, data=True, language=language
        )
        if note is not None:
            related_words_source_data[0]['note'] = note
            related_words_expected_data[0]['note'] = note
        source_json = {
            'language': word.language.name,
            'text': word.text,
            objs_related_name: related_words_source_data,
        }

        response = auth_api_client(user).post(
            self.endpoint, data=source_json, format='json'
        )
        response_words_content = json.loads(response.content)[objs_related_name]

        assert response.status_code == 201
        assert len(response_words_content) == len(related_words_expected_data)
        assert all(
            [
                response_words_content[0]['from_word'][field] == value
                for field, value in related_words_expected_data[0]['from_word'].items()
            ]
        )
        if note:
            assert (
                response_words_content[0]['note']
                == related_words_expected_data[0]['note']
            )

    def test_word_create_already_exist(self, auth_api_client, user, learning_language):
        """
        На запрос создания уже существующего слова с новыми данными возвращается
        ошибка 409.
        """
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)
        source_json = {
            'language': word.language.name,
            'text': word.text,
            'tags': [],
        }

        response = auth_api_client(user).post(
            self.endpoint, data=source_json, format='json'
        )

        assert response.status_code == 409
        assert (
            'detail' in response.data
        ), 'В ответе с кодом 409 должен возвращаться параметр `detail`.'
        assert (
            'existing_object' in response.data
        ), 'В ответе с кодом 409 должен возвращаться параметр `existing_object`.'

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name, related_model, update_attr',
        [
            ('translations', 'word_translations', WordTranslation, 'text'),
            ('examples', 'word_usage_examples', UsageExample, 'text'),
            ('definitions', 'word_definitions', Definition, 'text'),
            ('tags', 'word_tags', WordTag, 'name'),
            ('form_groups', 'word_form_groups', FormGroup, 'name'),
            ('synonyms', 'related_words_data', Word, 'text'),
            ('antonyms', 'related_words_data', Word, 'text'),
            ('forms', 'related_words_data', Word, 'text'),
            ('similars', 'related_words_data', Word, 'text'),
            ('collections', 'collections', Collection, 'title'),
        ],
    )
    def test_word_create_related_objs_already_exist(
        self,
        auth_api_client,
        user,
        learning_language,
        objs_related_name,
        fixture_name,
        related_model,
        update_attr,
        request,
    ):
        """
        На запрос создания слова с уже существующим вложенным объектом с
        новыми данными возвращается ошибка 409.
        """
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)
        obj = baker.make(related_model, author=user, _quantity=1)
        _, related_objs_source, _ = request.getfixturevalue(fixture_name)(
            user, data=True, make=True, language=language, word=word
        )
        related_objs_source[0][update_attr] = obj[0].__getattribute__(update_attr)
        source_json = {
            'language': word.language.name,
            'text': word.text,
            objs_related_name: related_objs_source,
        }

        response = auth_api_client(user).post(
            self.endpoint, data=source_json, format='json'
        )

        assert response.status_code == 409
        assert (
            'detail' in response.data
        ), 'В ответе с кодом 409 должен возвращаться параметр `detail`.'
        assert (
            'existing_object' in response.data
        ), 'В ответе с кодом 409 должен возвращаться параметр `existing_object`.'

    def test_word_create_not_auth(self, api_client):
        """
        На запрос создания слова от неавторизованного пользователя
        возвращается ошибка 401.
        """
        response = api_client().post(self.endpoint)

        assert response.status_code == 401

    def test_word_validate_language(self, auth_api_client, user):
        """Язык слова должен быть из изучаемых языков пользователя."""
        word = baker.make(Word, author=user)
        source_json = {
            'language': getattr(word.language, 'name', None),
            'text': word.text,
        }

        response = auth_api_client(user).post(
            self.endpoint, data=source_json, format='json'
        )

        assert response.status_code == 400
        assert (
            'language' in response.data
        ), 'В ответе с кодом 400 должно возвращаться поле `language`.'

    def test_word_validate_translations_language(
        self, auth_api_client, user, learning_language
    ):
        """Язык перевода должен быть из изучаемых или родных языков пользователя"""
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)
        translation = baker.make(WordTranslation, author=user)
        source_json = {
            'language': word.language.name,
            'text': word.text,
            'translations': [
                {
                    'language': getattr(translation.language, 'name', None),
                    'text': translation.text,
                }
            ],
        }

        response = auth_api_client(user).post(
            self.endpoint, data=source_json, format='json'
        )

        assert response.status_code == 400
        assert (
            'translations' in response.data
        ), 'В ответе с кодом 400 должно возвращаться поле `translations`.'

    @pytest.mark.parametrize(
        'objs_related_field, objs_data',
        [
            ('examples', [{'language': 'French', 'text': 'Some text'}]),
            ('definitions', [{'language': 'French', 'text': 'Some text'}]),
            ('synonyms', [{'from_word': {'language': 'French', 'text': 'Some text'}}]),
            ('antonyms', [{'from_word': {'language': 'French', 'text': 'Some text'}}]),
            ('forms', [{'from_word': {'language': 'French', 'text': 'Some text'}}]),
            ('similars', [{'from_word': {'language': 'French', 'text': 'Some text'}}]),
            ('form_groups', [{'language': 'French', 'name': 'Some text'}]),
        ],
    )
    def test_word_validate_related_objs_language(
        self, auth_api_client, user, objs_related_field, objs_data
    ):
        """Язык дополнений слова такой же, как у самого слова."""
        source_json = {
            'language': 'English',
            'text': 'Test word',
            objs_related_field: objs_data,
        }

        response = auth_api_client(user).post(
            self.endpoint, data=source_json, format='json'
        )

        assert response.status_code == 400

    def test_word_validate_text(self, auth_api_client, user):
        """При создании слова нельзя использовать неразрешенные символы."""
        source_json = {
            'language': 'English',
            'text': 'Some forbidden symbols: 123%$#@*&^<>/|\\',
        }

        response = auth_api_client(user).post(
            self.endpoint, data=source_json, format='json'
        )

        assert response.status_code == 400

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name, limit',
        [
            (
                'translations',
                'word_translations',
                AmountLimits.Vocabulary.MAX_TRANSLATIONS_AMOUNT,
            ),
            (
                'examples',
                'word_usage_examples',
                AmountLimits.Vocabulary.MAX_EXAMPLES_AMOUNT,
            ),
            (
                'definitions',
                'word_definitions',
                AmountLimits.Vocabulary.MAX_DEFINITIONS_AMOUNT,
            ),
            ('types', 'word_types', AmountLimits.Vocabulary.MAX_TYPES_AMOUNT),
            ('tags', 'word_tags', AmountLimits.Vocabulary.MAX_TAGS_AMOUNT),
            (
                'form_groups',
                'word_form_groups',
                AmountLimits.Vocabulary.MAX_FORM_GROUPS_AMOUNT,
            ),
            (
                'synonyms',
                'related_words_data',
                AmountLimits.Vocabulary.MAX_SYNONYMS_AMOUNT,
            ),
            (
                'antonyms',
                'related_words_data',
                AmountLimits.Vocabulary.MAX_ANTONYMS_AMOUNT,
            ),
            ('forms', 'related_words_data', AmountLimits.Vocabulary.MAX_FORMS_AMOUNT),
            (
                'similars',
                'related_words_data',
                AmountLimits.Vocabulary.MAX_SIMILARS_AMOUNT,
            ),
            # (
            #     'image_associations',
            #     'word_image_associations',
            #     AmountLimits.Vocabulary.MAX_IMAGES_AMOUNT,
            # ),
            (
                'quote_associations',
                'word_quote_associations',
                AmountLimits.Vocabulary.MAX_QUOTES_AMOUNT,
            ),
        ],
    )
    def test_word_validate_related_objs_amount(
        self,
        auth_api_client,
        user,
        learning_language,
        objs_related_name,
        fixture_name,
        limit,
        request,
    ):
        """Кол-во дополнений слова не превышает заданных лимитов."""
        language = learning_language(user)
        word = baker.prepare(Word, author=user, language=language)
        _, related_objs_source_data, _ = request.getfixturevalue(fixture_name)(
            user, data=True, language=language, _quantity=limit + 1
        )
        source_json = {
            'language': word.language.name,
            'text': word.text,
            objs_related_name: related_objs_source_data,
        }

        response = auth_api_client(user).post(
            self.endpoint, data=source_json, format='json'
        )

        assert response.status_code == 409

    def test_word_retrieve(self, auth_api_client, user, word):
        """При запросе от автора возвращает нужное слово."""
        word = word(user, make=True)

        response = auth_api_client(user).get(f'{self.endpoint}{word.slug}/')

        assert response.status_code == 200 or response.status_code == 301
        assert json.loads(response.content)['slug'] == word.slug

    def test_word_retrieve_not_auth(self, api_client):
        """
        На запрос получения слова от неавторизованного пользователя
        возвращается ошибка 401.
        """
        word = baker.make(Word)
        response = api_client().get(f'{self.endpoint}{word.slug}/')

        assert response.status_code == 401

    @pytest.mark.parametrize(
        'field, old_value, new_value, fixture_name',
        [
            ('text', 'word text', 'new word text', None),
            ('is_problematic', False, True, None),
            ('language', None, None, 'learning_language'),
            ('types', None, None, 'word_types'),
        ],
    )
    def test_word_partial_update_simple_data(
        self, auth_api_client, user, field, old_value, new_value, fixture_name, request
    ):
        """
        Слово успешно обновляется при запросе с валидными данными от авторизованного
        пользователя.
        """
        if fixture_name:
            old_value = request.getfixturevalue(fixture_name)(user)
            new_value = request.getfixturevalue(fixture_name)(
                user, data=True, source_only=True
            )
        word = baker.make(Word, author=user, **{field: old_value})
        update_data = {field: new_value}

        response = auth_api_client(user).patch(
            f'{self.endpoint}{word.slug}/',
            data=update_data,
            format='json',
        )

        assert response.status_code == 200 or response.status_code == 301
        assert response.data[field] == update_data[field]

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name, related_model, delete_extra_objs, res_name',
        [
            ('translations', 'word_translations', WordTranslation, True, ''),
            ('examples', 'word_usage_examples', UsageExample, True, ''),
            ('definitions', 'word_definitions', Definition, True, ''),
            ('tags', 'word_tags', WordTag, True, ''),
            ('collections', 'collections', Collection, False, ''),
            # (
            #     'image_associations',
            #     'word_image_associations',
            #     ImageAssociation,
            #     True,
            #     'associations',
            # ),
            (
                'quote_associations',
                'word_quote_associations',
                QuoteAssociation,
                True,
                'associations',
            ),
        ],
    )
    def test_word_partial_update_related_objs(
        self,
        auth_api_client,
        user,
        objs_related_name,
        fixture_name,
        related_model,
        delete_extra_objs,
        learning_language,
        res_name,
        request,
    ):
        """
        Вложенные объекты успешно обновляются при обновлении слова с валидными
        данными от авторизованного пользователя.
        """
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)
        old_objs = baker.make(related_model, author=user, _quantity=2)
        word.__getattribute__(objs_related_name).set(old_objs)
        _, new_objs_source_data, new_objs_expected_data = request.getfixturevalue(
            fixture_name
        )(user, data=True, language=language)

        response = auth_api_client(user).patch(
            f'{self.endpoint}{word.slug}/',
            data={objs_related_name: new_objs_source_data},
            format='json',
        )
        response_objs_content = json.loads(response.content)[
            res_name or objs_related_name
        ]

        assert response.status_code == 200 or response.status_code == 301
        assert len(response_objs_content) == 1
        assert all(
            [
                response_objs_content[0][field] == value
                for field, value in new_objs_expected_data[0].items()
            ]
        )
        if delete_extra_objs:
            assert not related_model.objects.filter(
                pk__in=[old_objs[0].id, old_objs[1].id], author=user
            ).exists()

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name, related_model',
        [
            ('synonyms', 'related_words_data', Word),
            ('antonyms', 'related_words_data', Word),
            ('forms', 'related_words_data', Word),
            ('similars', 'related_words_data', Word),
        ],
    )
    def test_word_partial_update_related_words(
        self,
        auth_api_client,
        user,
        objs_related_name,
        fixture_name,
        related_model,
        learning_language,
        request,
    ):
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)
        old_objs = baker.make(related_model, author=user, _quantity=2)
        word.__getattribute__(objs_related_name).set(old_objs)
        _, new_objs_source_data, new_objs_expected_data = request.getfixturevalue(
            fixture_name
        )(user, data=True, language=language)

        response = auth_api_client(user).patch(
            f'{self.endpoint}{word.slug}/',
            data={objs_related_name: new_objs_source_data},
            format='json',
        )
        response_objs_content = json.loads(response.content)[objs_related_name]

        assert response.status_code == 200 or response.status_code == 301
        assert len(response_objs_content) == 1
        assert all(
            [
                response_objs_content[0]['from_word'][field] == value
                for field, value in new_objs_expected_data[0]['from_word'].items()
            ]
        )

    def test_word_partial_update_favorite(self, auth_api_client, user):
        """
        Флажок `favorite` успешно обновляется при обновлении слова с валидными
        данными от авторизованного пользователя.
        """
        word = baker.make(Word, author=user)
        FavoriteWord.objects.create(word=word, user=user)
        update_data = {'favorite': False}

        response = auth_api_client(user).patch(
            f'{self.endpoint}{word.slug}/',
            data=update_data,
            format='json',
        )

        assert response.status_code == 200 or response.status_code == 301
        assert response.data['favorite'] == update_data['favorite']

    def test_word_partial_update_already_exist(self, auth_api_client, user):
        """
        На запрос редактирования текста слова при совпадении текста слова с другим
        словом возвращается ошибка 409.
        """
        existing_word = baker.make(Word, author=user, text='Same text')
        other_word = baker.make(Word, author=user)
        source_json = {'text': existing_word.text}

        response = auth_api_client(user).patch(
            f'{self.endpoint}{other_word.slug}/', data=source_json, format='json'
        )

        assert response.status_code == 409
        assert (
            'detail' in response.data
        ), 'В ответе с кодом 409 должен возвращаться параметр `detail`.'
        assert (
            'obj_lookup' in response.data['detail']
        ), 'В ответе с кодом 409 должен возвращаться параметр `obj_lookup`'

    def test_word_partial_update_not_auth(self, api_client):
        """
        На запрос обновления слова от неавторизованного пользователя
        возвращается ошибка 401.
        """
        word = baker.make(Word)
        response = api_client().patch(f'{self.endpoint}{word.slug}/')

        assert response.status_code == 401

    @pytest.mark.parametrize(
        'objs_related_name, related_model',
        [
            ('translations', WordTranslation),
            ('examples', UsageExample),
            ('definitions', Definition),
            ('tags', WordTag),
            ('form_groups', FormGroup),
            ('image_associations', ImageAssociation),
            ('quote_associations', QuoteAssociation),
        ],
    )
    def test_word_destroy(
        self, auth_api_client, user, objs_related_name, related_model
    ):
        """
        Слово успешно удаляется при запросе от автора.
        Связанные объекты также удалются, если не используются в других словах.
        """
        objs = baker.make(related_model, author=user, _quantity=2)
        word = baker.make(Word, author=user)
        word.__getattribute__(objs_related_name).set(objs)
        other_word = baker.make(Word, author=user)
        other_word.__getattribute__(objs_related_name).add(objs[0])

        response = auth_api_client(user).delete(f'{self.endpoint}{word.slug}/')

        assert response.status_code in (204, 200, 301)
        assert not related_model.objects.filter(pk=objs[1].id, author=user).exists()
        assert related_model.objects.filter(pk=objs[0].id, author=user).exists()

    def test_word_destroy_not_auth(self, api_client):
        """
        На запрос удаления слова от неавторизованного пользователя
        возвращается ошибка 401.
        """
        word = baker.make(Word)

        response = api_client().delete(f'{self.endpoint}{word.slug}/')

        assert response.status_code == 401

    def test_random_word_action(self, auth_api_client, user):
        """
        Авторизованный пользователь успешно получает случайное слово из своего словаря.
        """
        baker.make(Word, author=user, _quantity=3)

        response = auth_api_client(user).get(f'{self.endpoint}random/')

        assert response.status_code == 200 or response.status_code == 301

    def test_random_word_action_not_auth(self, api_client):
        """
        На запрос получения случайного слова из своего словаря от неавторизованного
        пользователя возвращается ошибка 401.
        """
        response = api_client().get(f'{self.endpoint}random/')

        assert response.status_code == 401

    def test_problematic_toggle_action(self, auth_api_client, user):
        """
        Метка `проблемное` слова успешно меняет состояние при запросе от автора слова.
        """
        word = baker.make(Word, author=user, is_problematic=False)

        response = auth_api_client(user).post(
            f'{self.endpoint}{word.slug}/problematic-toggle/'
        )

        assert response.status_code == 201
        assert response.data['is_problematic'] is True

    def test_problematic_toggle_action_not_auth(self, api_client):
        """
        На запрос изменения метки `проблемное` слова от неавторизованного пользователя
        возвращается ошибка 401.
        """
        word = baker.make(Word)

        response = api_client().post(f'{self.endpoint}{word.slug}/problematic-toggle/')

        assert response.status_code == 401

    def test_multiple_words_create_action(
        self, auth_api_client, user, learning_language
    ):
        """
        Слова успешно создаются при множественном создании при запросе от
        авторизованного пользователя, в ответе возвращается весь словарь пользователя.
        """
        language = learning_language(user)
        existing_word = baker.make(Word, author=user, language=language)
        new_word = baker.prepare(Word, author=user, language=language)
        existing_collection = baker.make(Collection, author=user)
        new_collection = baker.prepare(Collection, author=user)
        source_data = {
            'words': [
                {
                    'text': existing_word.text,
                    'language': existing_word.language.name,
                },
                {
                    'text': new_word.text,
                    'language': new_word.language.name,
                },
            ],
            'collections': [
                {
                    'title': existing_collection.title,
                    'description': existing_collection.description,
                },
                {
                    'title': new_collection.title,
                    'description': new_collection.description,
                },
            ],
        }

        response = auth_api_client(user).post(
            f'{self.endpoint}multiple-create/', data=source_data, format='json'
        )

        assert response.status_code == 201
        assert response.data['count'] == 2, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == 2
        assert (
            WordsInCollections.objects.filter(word__text=existing_word.text).count()
            == 2
        )
        assert WordsInCollections.objects.filter(word__text=new_word.text).count() == 2

    def test_multiple_words_create_already_exist(
        self, auth_api_client, user, learning_language
    ):
        """
        На запрос создания уже существующих слов с новыми данными
        возвращается ошибка 409.
        """
        language = learning_language(user)
        existing_word = baker.make(Word, author=user, language=language)
        existing_collection = baker.make(Collection, author=user)
        new_collection = baker.prepare(Collection, author=user)
        source_data = {
            'words': [
                {
                    'text': existing_word.text,
                    'language': existing_word.language.name,
                    'tags': [],
                },
            ],
            'collections': [
                {
                    'title': existing_collection.title,
                    'description': existing_collection.description,
                },
                {
                    'title': new_collection.title,
                    'description': new_collection.description,
                },
            ],
        }

        response = auth_api_client(user).post(
            f'{self.endpoint}multiple-create/', data=source_data, format='json'
        )

        assert response.status_code == 409

    def test_multiple_words_create_not_auth(self, api_client):
        """
        На запрос создания нескольких слов от неавторизованного пользователя
        возвращается ошибка 401.
        """
        response = api_client().post(f'{self.endpoint}multiple-create/', format='json')

        assert response.status_code == 401

    @pytest.mark.parametrize(
        'objs_related_name, related_model, res_name',
        [
            ('tags', WordTag, ''),
            ('translations', WordTranslation, ''),
            ('examples', UsageExample, ''),
            ('definitions', Definition, ''),
            ('synonyms', Word, ''),
            ('antonyms', Word, ''),
            ('similars', Word, ''),
            ('forms', Word, ''),
            ('collections', Collection, ''),
            ('image_associations', ImageAssociation, 'associations'),
            ('quote_associations', QuoteAssociation, 'associations'),
        ],
    )
    def test_related_objs_list_action(
        self, auth_api_client, user, objs_related_name, related_model, res_name
    ):
        """
        Список дополнений слова успешно возвращается при запросе от автора слова.
        """
        word = baker.make(Word, author=user)
        objs = baker.make(related_model, author=user, _quantity=2)
        word.__getattribute__(objs_related_name).set(objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{word.slug}/{res_name or objs_related_name}/',
            format='json',
        )

        assert response.status_code == 200
        assert response.data['count'] == 2
        assert len(response.data[res_name or objs_related_name]) == 2

    def test_translations_list_filter_by_language(
        self, auth_api_client, user, word_translations
    ):
        word = baker.make(Word, author=user)
        translation = word_translations(user, make=True)
        other_translation = word_translations(user, make=True)
        word.translations.add(*translation, *other_translation)

        response = auth_api_client(user).get(
            f'{self.endpoint}{word.slug}/translations/',
            {'language': translation[0].language.name},
            format='json',
        )

        assert response.status_code == 200
        assert response.data['count'] == 1, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['translations']) == 1

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name',
        [
            ('translations', 'word_translations'),
            ('examples', 'word_usage_examples'),
            ('definitions', 'word_definitions'),
            ('synonyms', 'related_words_data'),
            ('antonyms', 'related_words_data'),
            ('forms', 'related_words_data'),
            ('similars', 'related_words_data'),
            ('collections', 'collections'),
        ],
    )
    def test_related_objs_create_action(
        self,
        auth_api_client,
        user,
        objs_related_name,
        fixture_name,
        learning_language,
        request,
    ):
        """
        Дополнения слова успешно создаются при запросе с валидными данными
        от автора слова.
        """
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)
        objs_quantity = 2
        _, source_data, _ = request.getfixturevalue(fixture_name)(
            user, data=True, make=False, language=language, _quantity=objs_quantity
        )

        response = auth_api_client(user).post(
            f'{self.endpoint}{word.slug}/{objs_related_name}/',
            data=source_data,
            format='json',
        )

        assert response.status_code == 201
        assert response.data[f'{objs_related_name}_count'] == objs_quantity
        assert len(response.data[objs_related_name]) == objs_quantity

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name, res_name',
        [
            ('translations', 'word_translations', ''),
            ('examples', 'word_usage_examples', ''),
            ('definitions', 'word_definitions', ''),
            # ('image_associations', 'word_image_associations', 'images'),
            ('quote_associations', 'word_quote_associations', 'quotes'),
        ],
    )
    def test_related_objs_retrieve_action(
        self,
        auth_api_client,
        user,
        objs_related_name,
        fixture_name,
        res_name,
        request,
    ):
        word = baker.make(Word, author=user)
        other_word = baker.make(Word, author=user)
        objs, _, expected_data = request.getfixturevalue(fixture_name)(
            user, word=word, data=True, make=True, _quantity=1
        )
        word.__getattribute__(objs_related_name).add(*objs)
        other_word.__getattribute__(objs_related_name).add(*objs)

        try:
            response = auth_api_client(user).get(
                f'{self.endpoint}{word.slug}/{res_name or objs_related_name}/{objs[0].slug}/',
            )
        except AttributeError:
            response = auth_api_client(user).get(
                f'{self.endpoint}{word.slug}/{res_name or objs_related_name}/{objs[0].id}/',
            )

        assert response.status_code == 200
        assert all(
            [response.data[field] == value for field, value in expected_data[0].items()]
        )

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name',
        [
            ('synonyms', 'related_words_data'),
            ('antonyms', 'related_words_data'),
            ('forms', 'related_words_data'),
            ('similars', 'related_words_data'),
        ],
    )
    def test_related_words_retrieve_action(
        self, auth_api_client, user, objs_related_name, fixture_name, request
    ):
        word = baker.make(Word, author=user)
        other_word = baker.make(Word, author=user)
        objs, _, expected_data = request.getfixturevalue(fixture_name)(
            user, data=True, make=True, _quantity=1
        )
        word.__getattribute__(objs_related_name).add(*objs)
        other_word.__getattribute__(objs_related_name).add(*objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{word.slug}/{objs_related_name}/{objs[0].slug}/',
        )

        assert response.status_code == 200
        assert all(
            [
                response.data['from_word'][field] == value
                for field, value in expected_data[0]['from_word'].items()
            ]
        )

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name, res_name',
        [
            ('translations', 'word_translations', ''),
            ('examples', 'word_usage_examples', ''),
            ('definitions', 'word_definitions', ''),
            # ('image_associations', 'word_image_associations', 'images'),
            ('quote_associations', 'word_quote_associations', 'quotes'),
        ],
    )
    def test_related_objs_partial_update_action(
        self,
        auth_api_client,
        user,
        objs_related_name,
        fixture_name,
        res_name,
        learning_language,
        request,
    ):
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)
        objs = request.getfixturevalue(fixture_name)(user, make=True, language=language)
        word.__getattribute__(objs_related_name).add(*objs)
        _, source_data, expected_data = request.getfixturevalue(fixture_name)(
            user, data=True, make=False, language=language, serializer_data=True
        )
        try:
            lookup = objs[0].slug
        except AttributeError:
            lookup = objs[0].id

        response = auth_api_client(user).patch(
            f'{self.endpoint}{word.slug}/{res_name or objs_related_name}/{lookup}/',
            data=source_data[0],
            format='json',
        )

        assert response.status_code == 200 or response.status_code == 301
        assert all(
            [response.data[field] == value for field, value in expected_data[0].items()]
        )

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name',
        [
            ('synonyms', 'related_words_data'),
            ('antonyms', 'related_words_data'),
            ('forms', 'related_words_data'),
            ('similars', 'related_words_data'),
        ],
    )
    def test_related_words_partial_update_action(
        self,
        auth_api_client,
        user,
        objs_related_name,
        fixture_name,
        learning_language,
        request,
    ):
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)
        objs = request.getfixturevalue(fixture_name)(user, make=True, language=language)
        word.__getattribute__(objs_related_name).add(*objs)

        _, source_data, expected_data = request.getfixturevalue(fixture_name)(
            user, data=True, make=False, language=language, serializer=True
        )

        try:
            lookup = objs[0].slug
        except AttributeError:
            lookup = objs[0].id

        response = auth_api_client(user).patch(
            f'{self.endpoint}{word.slug}/{objs_related_name}/{lookup}/',
            data=source_data[0],
            format='json',
        )

        assert response.status_code == 200 or response.status_code == 301
        assert all(
            [
                response.data['from_word'][field] == value
                for field, value in expected_data[0]['from_word'].items()
            ]
        )

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name, res_name',
        [
            ('translations', 'word_translations', ''),
            ('examples', 'word_usage_examples', ''),
            ('definitions', 'word_definitions', ''),
            # ('image_associations', 'word_image_associations', 'images'),
            ('quote_associations', 'word_quote_associations', 'quotes'),
            ('synonyms', 'related_words_data', ''),
            ('antonyms', 'related_words_data', ''),
            ('forms', 'related_words_data', ''),
            ('similars', 'related_words_data', ''),
        ],
    )
    def test_related_objs_destroy_action(
        self,
        auth_api_client,
        user,
        objs_related_name,
        fixture_name,
        res_name,
        learning_language,
        request,
    ):
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)
        objs = request.getfixturevalue(fixture_name)(
            user, make=True, word=word, language=language, _quantity=2
        )
        word.__getattribute__(objs_related_name).set(objs)

        try:
            lookup = objs[0].slug
        except AttributeError:
            lookup = objs[0].id

        response = auth_api_client(user).delete(
            f'{self.endpoint}{word.slug}/{res_name or objs_related_name}/{lookup}/'
        )

        assert response.status_code in (204, 200)
        if response.data and 'count' in response.data:
            assert response.data['count'] == 1

    # images upload

    def test_word_favorites_list_action(self, auth_api_client, user, learning_language):
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)
        FavoriteWord.objects.create(user=user, word=word)

        response = auth_api_client(user).get(f'{self.endpoint}favorites/')

        assert response.data['count'] == 1

    def test_word_favorite_create_action(
        self, auth_api_client, user, learning_language
    ):
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)

        response = auth_api_client(user).post(f'{self.endpoint}{word.slug}/favorite/')

        assert FavoriteWord.objects.filter(user=user, word=word).exists()

    def test_word_favorite_destroy_action(
        self, auth_api_client, user, learning_language
    ):
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)

        response = auth_api_client(user).delete(f'{self.endpoint}{word.slug}/favorite/')

        assert not FavoriteWord.objects.filter(user=user, word=word).exists()


@pytest.mark.word_types
class TestTypesEndpoints:
    endpoint = '/api/types/'

    def test_list(self, auth_api_client, user, word_types):
        """
        По запросу типов слов и фраз возвращается список типов для авторизованного
        пользователя.
        """
        types = word_types()

        response = auth_api_client(user).get(self.endpoint)

        assert response.status_code == 200
        assert len(response.data) == len(types)


@pytest.mark.word_tags
class TestTagsEndpoints:
    endpoint = '/api/tags/'

    def test_list(self, auth_api_client, user, word_tags):
        """
        По запросу тегов слов и фраз пользователя возвращается список тегов авторизованного
        пользователя.
        """
        tags = word_tags(user, make=True)

        response = auth_api_client(user).get(self.endpoint)

        assert response.status_code == 200
        assert len(response.data) == len(tags)


@pytest.mark.word_form_groups
class TestFormGroupsEndpoints:
    endpoint = '/api/forms-groups/'

    def test_list(self, auth_api_client, user, word_form_groups):
        """
        По запросу групп форм слов и фраз пользователя возвращается список групп форм слов
        авторизованного пользователя.
        """
        form_groups = word_form_groups(user, make=True)

        response = auth_api_client(user).get(self.endpoint)

        assert response.status_code == 200
        assert len(response.data) == len(form_groups)


@pytest.mark.word_translations
class TestWordTranslationsEndpoints:
    endpoint = '/api/translations/'
    objs_related_name = 'translations'
    related_model = WordTranslation

    @pytest.mark.parametrize(
        'pagination_field',
        [
            ('count'),
            ('next'),
            ('previous'),
            ('results'),
        ],
    )
    def test_list(self, auth_api_client, user, pagination_field, word_translations):
        """
        По запросу переводов слов и фраз пользователя возвращается список переводов слов
        авторизованного пользователяс с пагинацией.
        """
        objs = word_translations(user, make=True)

        response = auth_api_client(user).get(self.endpoint)

        assert response.status_code == 200
        assert pagination_field in response.data, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются данные с пагинацией. '
            f'Не найден параметр `{pagination_field}`'
        )
        assert response.data['count'] == len(objs), (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == len(objs)

    def test_create(
        self,
        auth_api_client,
        user,
        word_translations,
        native_language,
        words_simple_data,
    ):
        language = native_language(user)
        _, source_data, expected_data = word_translations(
            user, make=False, data=True, language=language
        )
        _, source_data[0]['words'], _ = words_simple_data(user, make=False, data=True)

        response = auth_api_client(user).post(
            self.endpoint,
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == len(source_data[0]['words'])

    def test_retrieve(self, auth_api_client, user, word_translations):
        objs, _, expected_data = word_translations(user, make=True, data=True)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{objs[0].slug}/',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_partial_update(self, auth_api_client, user, word_translations):
        objs = word_translations(user, make=True)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)
        _, source_data, expected_data = word_translations(user, make=False, data=True)
        expected_data[0].pop('language')

        response = auth_api_client(user).patch(
            f'{self.endpoint}{objs[0].slug}/',
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_delete(self, auth_api_client, user, word_translations):
        objs = word_translations(user, make=True)

        response = auth_api_client(user).delete(
            f'{self.endpoint}{objs[0].slug}/',
        )

        assert response.status_code in (204, 200)
        assert not self.related_model.objects.filter(slug=objs[0].slug).exists()

    def test_add_words_to_translation(
        self,
        auth_api_client,
        user,
        word_translations,
        native_language,
        words_simple_data,
    ):
        language = native_language(user)
        objs = word_translations(user, make=True, data=False, language=language)
        _, source_data, _ = words_simple_data(user, make=False, data=True)

        response = auth_api_client(user).post(
            f'{self.endpoint}{objs[0].slug}/add-words/',
            data=source_data,
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert response_content['words']['count'] == len(source_data)


@pytest.mark.word_usage_examples
class TestWordExamplesEndpoints:
    endpoint = '/api/examples/'
    objs_related_name = 'examples'
    related_model = UsageExample

    @pytest.mark.parametrize(
        'pagination_field',
        [
            ('count'),
            ('next'),
            ('previous'),
            ('results'),
        ],
    )
    def test_list(self, auth_api_client, user, pagination_field, word_usage_examples):
        """
        По запросу примеров слов и фраз пользователя возвращается список примеров слов
        авторизованного пользователяс с пагинацией.
        """
        objs = word_usage_examples(user, make=True)

        response = auth_api_client(user).get(self.endpoint)

        assert response.status_code == 200
        assert pagination_field in response.data, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются данные с пагинацией. '
            f'Не найден параметр `{pagination_field}`'
        )
        assert response.data['count'] == len(objs), (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == len(objs)

    def test_create(
        self,
        auth_api_client,
        user,
        word_usage_examples,
        learning_language,
        words_simple_data,
    ):
        language = learning_language(user)
        _, source_data, expected_data = word_usage_examples(
            user, make=False, data=True, language=language
        )
        _, source_data[0]['words'], _ = words_simple_data(
            user, make=False, data=True, language=language
        )

        response = auth_api_client(user).post(
            self.endpoint,
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == len(source_data[0]['words'])

    def test_retrieve(self, auth_api_client, user, word_usage_examples):
        objs, _, expected_data = word_usage_examples(user, make=True, data=True)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{objs[0].slug}/',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_partial_update(self, auth_api_client, user, word_usage_examples):
        objs = word_usage_examples(user, make=True, data=False)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)
        _, source_data, expected_data = word_usage_examples(user, make=False, data=True)
        expected_data[0].pop('language')

        response = auth_api_client(user).patch(
            f'{self.endpoint}{objs[0].slug}/',
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_delete(self, auth_api_client, user, word_usage_examples):
        objs = word_usage_examples(user, make=True)

        response = auth_api_client(user).delete(
            f'{self.endpoint}{objs[0].slug}/',
        )

        assert response.status_code in (204, 200)
        assert not self.related_model.objects.filter(slug=objs[0].slug).exists()

    def test_add_words_to_example(
        self,
        auth_api_client,
        user,
        word_usage_examples,
        learning_language,
        words_simple_data,
    ):
        language = learning_language(user)
        objs = word_usage_examples(user, make=True, data=False, language=language)
        _, source_data, _ = words_simple_data(
            user, make=False, data=True, language=language
        )

        response = auth_api_client(user).post(
            f'{self.endpoint}{objs[0].slug}/add-words/',
            data=source_data,
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert response_content['words']['count'] == len(source_data)


@pytest.mark.word_definitions
class TestWordDefinitionsEndpoints:
    endpoint = '/api/definitions/'
    objs_related_name = 'definitions'
    related_model = Definition

    @pytest.mark.parametrize(
        'pagination_field',
        [
            ('count'),
            ('next'),
            ('previous'),
            ('results'),
        ],
    )
    def test_list(self, auth_api_client, user, pagination_field, word_definitions):
        """
        По запросу определений слов и фраз пользователя возвращается список определений слов
        авторизованного пользователяс с пагинацией.
        """
        objs = word_definitions(user, make=True)

        response = auth_api_client(user).get(self.endpoint)

        assert response.status_code == 200
        assert pagination_field in response.data, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются данные с пагинацией. '
            f'Не найден параметр `{pagination_field}`'
        )
        assert response.data['count'] == len(objs), (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == len(objs)

    def test_create(
        self,
        auth_api_client,
        user,
        word_definitions,
        learning_language,
        words_simple_data,
    ):
        language = learning_language(user)
        _, source_data, expected_data = word_definitions(
            user, make=False, data=True, language=language
        )
        _, source_data[0]['words'], _ = words_simple_data(
            user, make=False, data=True, language=language
        )

        response = auth_api_client(user).post(
            self.endpoint,
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == len(source_data[0]['words'])

    def test_retrieve(self, auth_api_client, user, word_definitions):
        objs, _, expected_data = word_definitions(user, make=True, data=True)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{objs[0].slug}/',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_partial_update(self, auth_api_client, user, word_definitions):
        objs = word_definitions(user, make=True, data=False)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)
        _, source_data, expected_data = word_definitions(user, make=False, data=True)
        expected_data[0].pop('language')

        response = auth_api_client(user).patch(
            f'{self.endpoint}{objs[0].slug}/',
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_delete(self, auth_api_client, user, word_definitions):
        objs = word_definitions(user, make=True)

        response = auth_api_client(user).delete(
            f'{self.endpoint}{objs[0].slug}/',
        )

        assert response.status_code in (204, 200)
        assert not self.related_model.objects.filter(slug=objs[0].slug).exists()

    def test_add_words_to_definition(
        self,
        auth_api_client,
        user,
        word_definitions,
        learning_language,
        words_simple_data,
    ):
        language = learning_language(user)
        objs = word_definitions(user, make=True, data=False, language=language)
        _, source_data, _ = words_simple_data(
            user, make=False, data=True, language=language
        )

        response = auth_api_client(user).post(
            f'{self.endpoint}{objs[0].slug}/add-words/',
            data=source_data,
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert response_content['words']['count'] == len(source_data)


@pytest.mark.word_synonyms
class TestWordSynonymsEndpoints:
    endpoint = '/api/synonyms/'
    objs_related_name = 'synonyms'
    related_model = Word

    def test_retrieve(self, auth_api_client, user, words_simple_data):
        objs, _, expected_data = words_simple_data(user, make=True, data=True)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{objs[0].slug}/',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_partial_update(self, auth_api_client, user, words_simple_data):
        objs = words_simple_data(user, make=True, data=False)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)
        _, source_data, expected_data = words_simple_data(user, make=False, data=True)
        expected_data[0].pop('language')

        response = auth_api_client(user).patch(
            f'{self.endpoint}{objs[0].slug}/',
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_delete(self, auth_api_client, user, words_simple_data):
        objs = words_simple_data(user, make=True, data=False)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)

        response = auth_api_client(user).delete(
            f'{self.endpoint}{objs[0].slug}/',
        )

        assert response.status_code in (204, 200)
        assert not self.related_model.objects.filter(slug=objs[0].slug).exists()

    def test_add_words_to_synonym(
        self, auth_api_client, user, learning_language, words_simple_data
    ):
        language = learning_language(user)
        objs = words_simple_data(user, make=True, data=False, language=language)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)
        _, source_data, _ = words_simple_data(
            user, make=False, data=True, language=language
        )

        response = auth_api_client(user).post(
            f'{self.endpoint}{objs[0].slug}/add-words/',
            data=source_data,
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert response_content['words']['count'] == len(source_data) + 1


@pytest.mark.word_antonyms
class TestWordAntonymsEndpoints:
    endpoint = '/api/antonyms/'
    objs_related_name = 'antonyms'
    related_model = Word

    def test_retrieve(self, auth_api_client, user, words_simple_data):
        objs, _, expected_data = words_simple_data(user, make=True, data=True)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{objs[0].slug}/',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_partial_update(self, auth_api_client, user, words_simple_data):
        objs = words_simple_data(user, make=True, data=False)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)
        _, source_data, expected_data = words_simple_data(user, make=False, data=True)
        expected_data[0].pop('language')

        response = auth_api_client(user).patch(
            f'{self.endpoint}{objs[0].slug}/',
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_delete(self, auth_api_client, user, words_simple_data):
        objs = words_simple_data(user, make=True, data=False)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)

        response = auth_api_client(user).delete(
            f'{self.endpoint}{objs[0].slug}/',
        )

        assert response.status_code in (204, 200)
        assert not self.related_model.objects.filter(slug=objs[0].slug).exists()

    def test_add_words_to_antonym(
        self, auth_api_client, user, learning_language, words_simple_data
    ):
        language = learning_language(user)
        objs = words_simple_data(user, make=True, data=False, language=language)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)
        _, source_data, _ = words_simple_data(
            user, make=False, data=True, language=language
        )

        response = auth_api_client(user).post(
            f'{self.endpoint}{objs[0].slug}/add-words/',
            data=source_data,
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert response_content['words']['count'] == len(source_data) + 1


@pytest.mark.word_similars
class TestWordSimilarsEndpoints:
    endpoint = '/api/similars/'
    objs_related_name = 'similars'
    related_model = Word

    def test_retrieve(self, auth_api_client, user, words_simple_data):
        objs, _, expected_data = words_simple_data(user, make=True, data=True)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{objs[0].slug}/',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_partial_update(self, auth_api_client, user, words_simple_data):
        objs = words_simple_data(user, make=True, data=False)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)
        _, source_data, expected_data = words_simple_data(user, make=False, data=True)
        expected_data[0].pop('language')

        response = auth_api_client(user).patch(
            f'{self.endpoint}{objs[0].slug}/',
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_delete(self, auth_api_client, user, words_simple_data):
        objs = words_simple_data(user, make=True, data=False)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)

        response = auth_api_client(user).delete(
            f'{self.endpoint}{objs[0].slug}/',
        )

        assert response.status_code in (204, 200)
        assert not self.related_model.objects.filter(slug=objs[0].slug).exists()

    def test_add_words_to_similar(
        self, auth_api_client, user, learning_language, words_simple_data
    ):
        language = learning_language(user)
        objs = words_simple_data(user, make=True, data=False, language=language)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)
        _, source_data, _ = words_simple_data(
            user, make=False, data=True, language=language
        )

        response = auth_api_client(user).post(
            f'{self.endpoint}{objs[0].slug}/add-words/',
            data=source_data,
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert response_content['words']['count'] == len(source_data) + 1


# @pytest.mark.word_images
# class TestWordImagesEndpoints:
#     endpoint = '/api/images/'
#     objs_related_name = 'image_associations'
#     related_model = ImageAssociation

#     @pytest.mark.parametrize(
#         'pagination_field',
#         [
#             ('count'),
#             ('next'),
#             ('previous'),
#             ('results'),
#         ],
#     )
#     def test_list(
#         self, auth_api_client, user, pagination_field, word_image_associations
#     ):
#         """
#         По запросу картинок-ассоциаций слов и фраз пользователя возвращается список картинок-ассоциаций слов
#         авторизованного пользователяс с пагинацией.
#         """
#         objs = word_image_associations(user, make=True)

#         response = auth_api_client(user).get(self.endpoint)

#         assert response.status_code == 200
#         assert pagination_field in response.data, (
#             f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются данные с пагинацией. '
#             f'Не найден параметр `{pagination_field}`'
#         )
#         assert response.data['count'] == len(objs), (
#             f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
#             f'Значение параметра `count` неправильное'
#         )
#         assert len(response.data['results']) == len(objs)

#     # def test_create(self, auth_api_client, user, word_image_associations, learning_language, words_simple_data):
#     #     language = learning_language(user)
#     #     _, source_data, expected_data = word_image_associations(
#     #         user, make=False, data=True, language=language
#     #     )
#     #     _, source_data[0]['words'], _ = words_simple_data(
#     #         user, make=False, data=True, language=language
#     #     )

#     #     response = auth_api_client(user).post(
#     #         self.endpoint,
#     #         data=source_data[0],
#     #         format='json',
#     #     )
#     #     response_content = json.loads(response.content)

#     #     assert response.status_code == 201
#     #     assert all([response_content[field] == value for field, value in expected_data[0].items()])
#     #     assert response_content['words']['count'] == len(source_data[0]['words'])

#     def test_retrieve(self, auth_api_client, user, word_image_associations):
#         objs, _, expected_data = word_image_associations(user, make=True, data=True)
#         word = baker.make(Word, author=user)
#         word.__getattribute__(self.objs_related_name).set(objs)

#         response = auth_api_client(user).get(
#             f'{self.endpoint}{objs[0].id}/',
#         )
#         response_content = json.loads(response.content)

#         assert response.status_code == 200
#         assert all(
#             [
#                 response_content[field] == value
#                 for field, value in expected_data[0].items()
#             ]
#         )
#         assert response_content['words']['count'] == 1

#     def test_partial_update(self, auth_api_client, user, word_image_associations):
#         objs = word_image_associations(user, make=True, data=False)
#         word = baker.make(Word, author=user)
#         word.__getattribute__(self.objs_related_name).set(objs)
#         _, source_data, expected_data = word_image_associations(
#             user, make=False, data=True, serializer_data=True
#         )

#         response = auth_api_client(user).patch(
#             f'{self.endpoint}{objs[0].id}/',
#             data=source_data[0],
#             format='json',
#         )
#         response_content = json.loads(response.content)

#         assert response.status_code == 200
#         assert all(
#             [
#                 response_content[field] == value
#                 for field, value in expected_data[0].items()
#             ]
#         )
#         assert response_content['words']['count'] == 1

#     def test_delete(self, auth_api_client, user, word_image_associations):
#         objs = word_image_associations(user, make=True)

#         response = auth_api_client(user).delete(
#             f'{self.endpoint}{objs[0].id}/',
#         )

#         assert response.status_code in (204, 200)
#         assert not self.related_model.objects.filter(id=objs[0].id).exists()

#     def test_add_words_to_image(
#         self, auth_api_client, user, word_image_associations, words_simple_data
#     ):
#         objs = word_image_associations(user, make=True, data=False)
#         _, source_data, _ = words_simple_data(user, make=False, data=True)

#         response = auth_api_client(user).post(
#             f'{self.endpoint}{objs[0].id}/add-words/',
#             data=source_data,
#             format='json',
#         )
#         response_content = json.loads(response.content)

#         assert response.status_code == 201
#         assert response_content['words']['count'] == len(source_data)


@pytest.mark.word_quotes
class TestWordQuoteEndpoints:
    endpoint = '/api/quotes/'
    objs_related_name = 'quote_associations'
    related_model = QuoteAssociation

    # def test_create(self, auth_api_client, user, word_image_associations, learning_language, words_simple_data):
    #     language = learning_language(user)
    #     _, source_data, expected_data = word_image_associations(
    #         user, make=False, data=True, language=language
    #     )
    #     _, source_data[0]['words'], _ = words_simple_data(
    #         user, make=False, data=True, language=language
    #     )

    #     response = auth_api_client(user).post(
    #         self.endpoint,
    #         data=source_data[0],
    #         format='json',
    #     )
    #     response_content = json.loads(response.content)

    #     assert response.status_code == 201
    #     assert all([response_content[field] == value for field, value in expected_data[0].items()])
    #     assert response_content['words']['count'] == len(source_data[0]['words'])

    def test_retrieve(self, auth_api_client, user, word_quote_associations):
        objs, _, expected_data = word_quote_associations(user, make=True, data=True)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{objs[0].id}/',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_partial_update(self, auth_api_client, user, word_quote_associations):
        objs = word_quote_associations(user, make=True, data=False)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)
        _, source_data, expected_data = word_quote_associations(
            user, make=False, data=True
        )

        response = auth_api_client(user).patch(
            f'{self.endpoint}{objs[0].id}/',
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_delete(self, auth_api_client, user, word_quote_associations):
        objs = word_quote_associations(user, make=True)

        response = auth_api_client(user).delete(
            f'{self.endpoint}{objs[0].id}/',
        )

        assert response.status_code in (204, 200)
        assert not self.related_model.objects.filter(id=objs[0].id).exists()

    def test_add_words_to_quote(
        self, auth_api_client, user, word_quote_associations, words_simple_data
    ):
        objs = word_quote_associations(user, make=True, data=False)
        _, source_data, _ = words_simple_data(user, make=False, data=True)

        response = auth_api_client(user).post(
            f'{self.endpoint}{objs[0].id}/add-words/',
            data=source_data,
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert response_content['words']['count'] == len(source_data)


@pytest.mark.main_page
class TestMainPageEndpoints:
    endpoint = '/api/main/'

    @pytest.mark.parametrize(
        'res_name, fixture_name',
        [
            ('words', 'words_simple_data'),
            ('collections', 'collections'),
            ('tags', 'word_tags'),
            # ('images', 'word_image_associations'),
            ('definitions', 'word_definitions'),
            ('examples', 'word_usage_examples'),
            ('translations', 'word_translations'),
        ],
    )
    def test_main_page_retrieve(
        self, auth_api_client, user, res_name, fixture_name, learning_language, request
    ):
        language = learning_language(user)
        objs, _, expected_data = request.getfixturevalue(fixture_name)(
            user, make=True, data=True, language=language
        )

        response = auth_api_client(user).get(self.endpoint)
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[f'last_10_{res_name}'][0][field] == value
                if field in response_content[f'last_10_{res_name}'][0]
                else True
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content[f'{res_name}_count'] == len(objs)
        assert len(response_content['learning_languages']) == 1
        assert response_content['learning_languages_count'] == 1


@pytest.mark.associations
class TestAssociationsEndpoints:
    endpoint = '/api/associations/'

    @pytest.mark.parametrize(
        'fixture_name',
        [
            # ('word_image_associations'),
            ('word_quote_associations'),
        ],
    )
    def test_list(self, auth_api_client, user, fixture_name, request):
        objs = request.getfixturevalue(fixture_name)(user, make=True, data=False)

        response = auth_api_client(user).get(self.endpoint)
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert len(response_content) == len(objs)


@pytest.mark.word_collections
class TestWordCollectionsEndpoints:
    endpoint = '/api/collections/'
    objs_related_name = 'collections'
    related_model = Collection

    @pytest.mark.parametrize(
        'pagination_field',
        [
            ('count'),
            ('next'),
            ('previous'),
            ('results'),
        ],
    )
    def test_list(self, auth_api_client, user, pagination_field, collections):
        """
        По запросу определений слов и фраз пользователя возвращается список определений слов
        авторизованного пользователяс с пагинацией.
        """
        objs = collections(user, make=True)

        response = auth_api_client(user).get(self.endpoint)

        assert response.status_code == 200
        assert pagination_field in response.data, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются данные с пагинацией. '
            f'Не найден параметр `{pagination_field}`'
        )
        assert response.data['count'] == len(objs), (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == len(objs)

    def test_create(self, auth_api_client, user, collections):
        _, source_data, expected_data = collections(user, make=False, data=True)

        response = auth_api_client(user).post(
            self.endpoint,
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )

    def test_retrieve(self, auth_api_client, user, collections):
        objs, _, expected_data = collections(user, make=True, data=True)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{objs[0].slug}/',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_partial_update(self, auth_api_client, user, collections):
        objs = collections(user, make=True, data=False)
        word = baker.make(Word, author=user)
        word.__getattribute__(self.objs_related_name).set(objs)
        _, source_data, expected_data = collections(user, make=False, data=True)

        response = auth_api_client(user).patch(
            f'{self.endpoint}{objs[0].slug}/',
            data=source_data[0],
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content[field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words']['count'] == 1

    def test_delete(self, auth_api_client, user, collections):
        objs = collections(user, make=True)

        response = auth_api_client(user).delete(
            f'{self.endpoint}{objs[0].slug}/',
        )

        assert response.status_code in (204, 200)
        assert not self.related_model.objects.filter(slug=objs[0].slug).exists()

    def test_add_words_to_collection(
        self, auth_api_client, user, collections, words_simple_data
    ):
        objs = collections(user, make=True, data=False)
        _, source_data, _ = words_simple_data(user, make=False, data=True)

        response = auth_api_client(user).post(
            f'{self.endpoint}{objs[0].slug}/add-words/',
            data=source_data,
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert response_content['words']['count'] == len(source_data)

    def test_add_words_to_collections(
        self, auth_api_client, user, collections, words_simple_data
    ):
        _, collections_source_data, _ = collections(user, make=False, data=True)
        _, words_source_data, _ = words_simple_data(user, make=False, data=True)
        source_data = {
            'words': words_source_data,
            'collections': collections_source_data,
        }

        response = auth_api_client(user).post(
            f'{self.endpoint}add-words-to-collections/',
            data=source_data,
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert response_content['words_added_count'] == len(words_source_data)
        assert response_content['collections_count'] == len(collections_source_data)
        assert response_content['count'] == len(words_source_data)
        assert len(response_content['results']) == len(words_source_data)

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name, res_name',
        [
            ('translations', 'word_translations', ''),
            ('examples', 'word_usage_examples', ''),
            ('definitions', 'word_definitions', ''),
            # ('image_associations', 'word_image_associations', 'images'),
        ],
    )
    def test_related_objs_retrieve(
        self,
        auth_api_client,
        user,
        learning_language,
        collections,
        objs_related_name,
        fixture_name,
        res_name,
        request,
    ):
        collections_objs = collections(user, make=True, data=False)
        language = learning_language(user)
        word = baker.make(Word, author=user, language=language)
        word.__getattribute__(self.objs_related_name).set(collections_objs)
        objs = request.getfixturevalue(fixture_name)(
            user, make=True, data=False, language=language
        )
        word.__getattribute__(objs_related_name).set(objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{collections_objs[0].slug}/{res_name or objs_related_name}/',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert response_content[objs_related_name]['count'] == len(objs)
        assert len(response_content[objs_related_name]['results']) == len(objs)

    # test_related_objs_search
    # test_related_objs_ordering
    # test_related_objs_filters

    def test_collection_favorites_list_action(self, auth_api_client, user, collections):
        collection = collections(user, make=True, data=False)[0]
        FavoriteCollection.objects.create(user=user, collection=collection)

        response = auth_api_client(user).get(f'{self.endpoint}favorites/')

        assert response.data['count'] == 1

    def test_collection_favorite_create_action(
        self, auth_api_client, user, collections
    ):
        collection = collections(user, make=True, data=False)[0]
        FavoriteCollection.objects.create(user=user, collection=collection)

        response = auth_api_client(user).post(
            f'{self.endpoint}{collection.slug}/favorite/'
        )

        assert FavoriteCollection.objects.filter(
            user=user, collection=collection
        ).exists()

    def test_collection_favorite_destroy_action(
        self, auth_api_client, user, collections
    ):
        collection = collections(user, make=True, data=False)[0]
        FavoriteCollection.objects.create(user=user, collection=collection)

        response = auth_api_client(user).delete(
            f'{self.endpoint}{collection.slug}/favorite/'
        )

        assert not FavoriteCollection.objects.filter(
            user=user, collection=collection
        ).exists()


@pytest.mark.languages
class TestLanguagesEndpoints:
    endpoint = '/api/languages/'

    def test_list_learning(self, auth_api_client, user, learning_languages):
        """
        По запросу списка языков пользователя возвращается список изучаемых языков
        авторизованного пользователя с счетчиком.
        """
        objs = learning_languages(user, data=False, _quantity=2)

        response = auth_api_client(user).get(self.endpoint)

        assert response.status_code == 200
        assert response.data['count'] == len(objs), (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == len(objs)

    def test_create(self, auth_api_client, user, languages):
        language_name = languages(name=True, extra_data={'learning_available': True})[0]
        source_data = [
            {
                'language': language_name,
                'level': 'some level',
            }
        ]

        response = auth_api_client(user).post(
            self.endpoint,
            data=source_data,
            format='json',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 201
        assert response_content['count'] == 1
        assert len(response_content['results']) == 1

    def test_create_amount_limit(self, auth_api_client, user, languages):
        language_names = languages(
            name=True,
            extra_data={'learning_available': True},
            _quantity=AmountLimits.Languages.MAX_LEARNING_LANGUAGES_AMOUNT + 1,
        )
        source_data = [
            {
                'language': language_name,
                'level': 'some level',
            }
            for language_name in language_names
        ]

        response = auth_api_client(user).post(
            self.endpoint,
            data=source_data,
            format='json',
        )

        assert response.status_code == 409

    def test_retrieve(self, auth_api_client, user, learning_languages):
        objs, _, expected_data = learning_languages(user, data=True, _quantity=1)
        baker.make(Word, author=user, language=objs[0].language)

        response = auth_api_client(user).get(
            f'{self.endpoint}{objs[0].language.name}/',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert all(
            [
                response_content['language'][field] == value
                for field, value in expected_data[0].items()
            ]
        )
        assert response_content['words_count'] == 1

    # retrieve words search, ordering, filters

    def test_delete(self, auth_api_client, user, learning_languages):
        language = learning_languages(user, data=False, _quantity=1)[0]

        response = auth_api_client(user).delete(
            f'{self.endpoint}{language.language.name}/',
        )

        assert response.status_code == 204
        assert not UserLearningLanguage.objects.filter(slug=language.slug).exists()

    @pytest.mark.parametrize(
        'objs_related_name, fixture_name, res_name',
        [
            ('collections', 'collections', ''),
        ],
    )
    def test_related_objs_retrieve(
        self,
        auth_api_client,
        user,
        learning_languages,
        objs_related_name,
        fixture_name,
        res_name,
        request,
    ):
        language = learning_languages(user, data=False, _quantity=1)[0]
        word = baker.make(Word, author=user, language=language.language)
        objs = request.getfixturevalue(fixture_name)(user, make=True, data=False)
        word.__getattribute__(objs_related_name).set(objs)

        response = auth_api_client(user).get(
            f'{self.endpoint}{language.language.name}/{res_name or objs_related_name}/',
        )
        response_content = json.loads(response.content)

        assert response.status_code == 200
        assert response_content[objs_related_name]['count'] == len(objs)
        assert len(response_content[objs_related_name]['results']) == len(objs)

    # retrieve collections search, ordering

    # get, post images choice

    def test_list_all(self, auth_api_client, user, languages):
        objs = languages(user, data=False, _quantity=2)

        response = auth_api_client(user).get(f'{self.endpoint}all/')

        assert response.status_code == 200
        assert len(response.data) == len(objs)

    def test_list_learning_available(self, auth_api_client, user, languages):
        objs = languages(
            name=False, extra_data={'learning_available': True}, _quantity=2
        )
        UserLearningLanguage.objects.create(user=user, language=objs[0])
        languages(user, data=False, _quantity=3)

        response = auth_api_client(user).get(f'{self.endpoint}learning-available/')

        assert response.status_code == 200
        assert response.data['count'] == len(objs) - 1, (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == len(objs) - 1

    def test_list_native(self, auth_api_client, user, native_languages):
        """
        По запросу списка родных языков пользователя возвращается список родных языков
        авторизованного пользователя с счетчиком.
        """
        objs = native_languages(user, data=False, _quantity=2)

        response = auth_api_client(user).get(
            f'{self.endpoint}native/',
        )

        assert response.status_code == 200
        assert response.data['count'] == len(objs), (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == len(objs)


@pytest.mark.global_languages
class TestGlobalLanguagesEndpoints:
    endpoint = '/api/global-languages/'

    def test_list(self, auth_api_client, user, languages):
        objs = languages(user, data=False, _quantity=2)

        response = auth_api_client(user).get(self.endpoint)

        assert response.status_code == 200
        assert len(response.data) == len(objs)

    def test_list_interface_available(self, auth_api_client, user, languages):
        objs = languages(
            name=False, extra_data={'interface_available': True}, _quantity=2
        )
        languages(user, data=False, _quantity=3)

        response = auth_api_client(user).get(f'{self.endpoint}interface/')

        assert response.status_code == 200
        assert response.data['count'] == len(objs), (
            f'Проверьте, что при GET запросе `{self.endpoint}` возвращаются правильные данные. '
            f'Значение параметра `count` неправильное'
        )
        assert len(response.data['results']) == len(objs)
