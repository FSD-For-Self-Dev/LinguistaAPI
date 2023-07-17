import datetime as dt
import json
import os
import re

import warnings
import factory
import pytest
from dotenv import load_dotenv

load_dotenv()

# from rest_framework.test import force_authenticate
from words.models import Collection, Tag, User, Word

from .conftest import auth_client
from .factories import (CollectionFactory, ExampleFactory, TagFactory,
                        TranslationFactory, UserFactory, WordFactory)

pytestmark = pytest.mark.django_db


class TestWordEndpoints:

    endpoint = '/api/words/'

    def test_list_not_auth(self, api_client):
        response = api_client().get(self.endpoint)
        assert response.status_code != 404, (
            'Страница {} не найдена, проверьте этот адрес в *urls.py*'.format(self.endpoint)
        )
        assert response.status_code == 401, (
            'Проверьте, что при GET запросе {} без токена авторизации '
            'возвращается статус 401'.format(self.endpoint)
        )

    def filter_test(self, filter_field, client, filter_value=None,
                    obj_data=None, factory=None, expected_amount=None):
        if obj_data:
            WordFactory.create(**obj_data) if not factory else factory.create(
                **obj_data
            )
        if filter_value is None:
            endpoint = self.endpoint + f'?{filter_field}={obj_data[filter_field]}'
        else:
            endpoint = self.endpoint + f'?{filter_field}={filter_value}'
        response = client.get(endpoint)
        data = json.loads(response.content)
        if expected_amount is None: expected_amount = 1
        assert len(data['results']) == expected_amount, (
            f'Проверьте, что при GET запросе `{endpoint}` '
            f'возвращаются отфильтрованные данные с пагинацией. '
            f'Значение параметра `results` не правильное'
        )

    def insensetive_test(self, client, search_value, expeted_min_amount):
        endpoint = self.endpoint + f'?search={search_value.capitalize()}'
        response = client.get(endpoint)
        data = json.loads(response.content)
        assert len(data['results']) >= expected_min_amount, (
            f'Проверьте, что при при GET запросе `{endpoint}` '
            f'поиск не чувствителен к регистру. '
            f'Значение параметра `results` не правильное'
        )

    def search_test(self, client, search_value, obj_data=None,
                    factory=None, expected_min_amount=None):
        if obj_data:
            WordFactory.create(**obj_data) if not factory else factory.create(
                **obj_data
            )
        endpoint = self.endpoint + f'?search={search_value}'
        if expected_min_amount is None: expected_min_amount = 1
        if (
            os.getenv('DB_NAME') == 'db.sqlite3' and 
            bool(re.search('[а-яА-Я]', search_value))
        ):
            warnings.warn(
                f'При использовании sqlite поиск нечувствителен к регистру '
                f'только при запросах на латинице. '
                f'GET запрос `{endpoint}` не будет работать корректно'
            )
        else:
            cases = (search_value.capitalize(), search_value.lower())
            for case in cases:
                endpoint = self.endpoint + f'?search={case}'
                response = client.get(endpoint)
                data = json.loads(response.content)
                assert len(data['results']) >= expected_min_amount, (
                    f'Проверьте, что при при GET запросе `{endpoint}` '
                    f'поиск не чувствителен к регистру. '
                    f'Значение параметра `results` не правильное'
                )
        response = client.get(endpoint)
        data = json.loads(response.content)
        assert len(data['results']) >= expected_min_amount, (
            f'Проверьте, что при GET запросе `{endpoint}` '
            f'возвращаются отфильтрованные данные с пагинацией. '
            f'Значение параметра `results` не правильное'
        )

    def ordering_test(self, client, ordering_field, expected_first,
                      expected_latest, expected_amount, order='asc'):
        ordered_query = Word.objects.order_by(ordering_field)
        expected_first = ordered_query.first()
        expected_latest = ordered_query.latest()
        # print(expected_first)
        if order == 'desc':
            ordering_field = '-' + ordering_field
            expected_first, expected_latest = expected_latest, expected_first
        endpoint = self.endpoint + f'?ordering={ordering_field}'
        response = client.get(endpoint)
        data = json.loads(response.content)
        first, latest = data['results'][0], data['results'][-1]
        assert len(data['results']) == expected_amount, (
            f'Проверьте, что при GET запросе `{endpoint}` '
            f'возвращаются отсортированные данные с пагинацией. '
            f'Значение параметра `results` не правильное'
        )
        # print(first, WordFactory.build(**first))
        assert first == expected_first, (
            f'Проверьте, что при GET запросе `{endpoint}` '
            f'возвращаются отсортированные данные с пагинацией. '
            f'Значение параметра `results` не правильное'
        )
        print('!')
        assert latest[ordering_field] == expected_latest[ordering_field], (
            f'Проверьте, что при GET запросе `{endpoint}` '
            f'возвращаются отсортированные данные с пагинацией. '
            f'Значение параметра `results` не правильное'
        )

    def test_list(self, api_client):
        # WordFactory.create_batch(3, tags=[TagFactory()], collections=[CollectionFactory()])

        author = UserFactory()
        WordFactory.create_batch(3, author=author)

        second_author = UserFactory()
        WordFactory(author=second_author)

        authed_client = auth_client(author)
        response = authed_client.get(self.endpoint)
        data = json.loads(response.content)

        assert response.status_code == 200
        assert 'count' in data, (
            'Проверьте, что при GET запросе `/api/words/` возвращаются данные с пагинацией. '
            'Не найден параметр `count`'
        )
        assert 'next' in data, (
            'Проверьте, что при GET запросе `/api/words/` возвращаются данные с пагинацией. '
            'Не найден параметр `next`'
        )
        assert 'previous' in data, (
            'Проверьте, что при GET запросе `/api/words/` возвращаются данные с пагинацией. '
            'Не найден параметр `previous`'
        )
        assert 'results' in data, (
            'Проверьте, что при GET запросе `/api/words/` возвращаются данные с пагинацией. '
            'Не найден параметр `results`'
        )
        assert data['count'] == 3, (
            'Проверьте, что при GET запросе `/api/words/` возвращаются данные с пагинацией. '
            'Значение параметра `count` не правильное'
        )
        assert len(data['results']) == 3, (
            'Проверьте, что при GET запросе `/api/words/` возвращаются данные с пагинацией. '
            'Значение параметра `results` не правильное'
        )
        # тесты фильтров
        self.filter_test(obj_data={
            'author': author,
            'status': 'USEFUL'
        }, filter_field='status', client=authed_client)
        self.filter_test(obj_data={
            'author': author,
            'language': 'en'
        }, filter_field='language', client=authed_client)
        self.filter_test(obj_data={
            'author': author,
            'tags': [TagFactory.create(name='easy')]
        }, filter_field='having_tag', filter_value='easy', client=authed_client)
        self.filter_test(obj_data={
            'author': author,
            'type': 'NOUN'
        }, filter_field='type', client=authed_client)
        self.filter_test(
            obj_data={
                'word': WordFactory.create(author=author),
                'translation': 'перевод'
            },
            filter_field='min_trnsl_count', filter_value=1,
            client=authed_client, factory=TranslationFactory
        )
        self.filter_test(
            filter_field='max_trnsl_count', filter_value=-1,
            client=authed_client, expected_amount=0
        )
        self.filter_test(
            obj_data={
                'word': WordFactory.create(author=author),
                'example': 'any sentence with word'
            },
            filter_field='min_exmpl_count', filter_value=1,
            client=authed_client, factory=ExampleFactory
        )
        self.filter_test(
            filter_field='max_exmpl_count', filter_value=-1,
            client=authed_client, expected_amount=0
        )
        now = dt.datetime.now().date().strftime('%Y-%m-%d')
        self.filter_test(
            filter_field='created_after', filter_value=now,
            client=authed_client, expected_amount=0
        )
        self.filter_test(
            filter_field='created_before', filter_value=now,
            client=authed_client, expected_amount=0
        )
        self.filter_test(
            filter_field='created', filter_value=now,
            client=authed_client,
            expected_amount=Word.objects.filter(author=author).count()
        )
        # тесты поиска
        self.search_test(
            obj_data={
                'author': author,
                'text': 'word'
            },
            search_value='word', client=authed_client
        )
        self.search_test(
            search_value='0', client=authed_client,
            expected_min_amount=0
        )
        self.search_test(
            search_value='easy', client=authed_client,
            expected_min_amount=1
        )
        self.search_test(
            search_value='перевод', client=authed_client,
            expected_min_amount=1
        )
        self.search_test(
            search_value='sentence with word', client=authed_client,
            expected_min_amount=1
        )
        self.search_test(
            obj_data={
                'author': author,
                'note': 'Примечание от автора'
            },
            search_value='Примечание', client=authed_client,
            expected_min_amount=1
        )
        # тесты сортировки
        # first, latest = Word.objects.aggregate(Max('created'))
        # assert False (print(first, latest))
        self.ordering_test(
            ordering_field='created', client=authed_client,
            expected_first=None, expected_latest=None,
            expected_amount=Word.objects.filter(author=author).count()
        )
        self.ordering_test(
            ordering_field='created', client=authed_client,
            expected_first=None, expected_latest=None, order='desc',
            expected_amount=Word.objects.filter(author=author).count()
        )

    # def test_create(self, api_client):
    #     currency = baker.prepare(Currency) 
    #     expected_json = {
    #         'name': currency.name,
    #         'code': currency.code,
    #         'symbol': currency.symbol
    #     }

    #     response = api_client().post(
    #         self.endpoint,
    #         data=expected_json,
    #         format='json'
    #     )

    #     assert response.status_code == 201
    #     assert json.loads(response.content) == expected_json

    # def test_retrieve(self, api_client):
    #     currency = baker.make(Currency)
    #     expected_json = {
    #         'name': currency.name,
    #         'code': currency.code,
    #         'symbol': currency.symbol
    #     }
    #     url = f'{self.endpoint}{currency.id}/'

    #     response = api_client().get(url)

    #     assert response.status_code == 200
    #     assert json.loads(response.content) == expected_json

    # @pytest.mark.parametrize('field',[
    #     ('code'),
    #     ('name'),
    #     ('symbol'),
    # ])
    # def test_partial_update(self, mocker, rf, field, api_client):
    #     currency = baker.make(Currency)
    #     currency_dict = {
    #         'code': currency.code,
    #         'name': currency.name,
    #         'symbol': currency.symbol
    #     } 
    #     valid_field = currency_dict[field]
    #     url = f'{self.endpoint}{currency.id}/'

    #     response = api_client().patch(
    #         url,
    #         {field: valid_field},
    #         format='json'
    #     )

    #     assert response.status_code == 200
    #     assert json.loads(response.content)[field] == valid_field

    # def test_delete(self, mocker, api_client):
    #     currency = baker.make(Currency)
    #     url = f'{self.endpoint}{currency.id}/'

    #     response = api_client().delete(url)

    #     assert response.status_code == 204
    #     assert Currency.objects.all().count() == 0

    # def test_random(self, mocker, api_client):
    #     currency = baker.make(Currency)
    #     url = f'{self.endpoint}{currency.id}/'

    #     response = api_client().delete(url)

    #     assert response.status_code == 204
    #     assert Currency.objects.all().count() == 0

    # def test_translations_list(self, mocker, api_client):
    #     currency = baker.make(Currency)
    #     url = f'{self.endpoint}{currency.id}/'

    #     response = api_client().delete(url)

    #     assert response.status_code == 204
    #     assert Currency.objects.all().count() == 0

    # def test_translations_create(self, mocker, api_client):
        # currency = baker.make(Currency)
        # url = f'{self.endpoint}{currency.id}/'

        # response = api_client().delete(url)

        # assert response.status_code == 204
        # assert Currency.objects.all().count() == 0
