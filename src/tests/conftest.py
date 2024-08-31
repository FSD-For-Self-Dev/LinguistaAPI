import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model
from model_bakery import baker

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient


@pytest.fixture
def auth_api_client():
    def get_auth_client(user):
        client = APIClient()
        token, _ = Token.objects.get_or_create(user=user)
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        return client

    return get_auth_client


@pytest.fixture
def user():
    return baker.make(User, username='test_user')
