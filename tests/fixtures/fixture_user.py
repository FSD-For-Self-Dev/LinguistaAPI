import pytest

@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username='TestUser', email='testuser@yamdb.fake', password='1234567'
    )

@pytest.fixture
def token_user(user):
    from rest_framework.authtoken.views import ObtainAuthToken, TokenAuthentication
    token = ObtainAuthToken.post(user)

    return {
        'access': str(token),
    }


@pytest.fixture
def user_client(token_user):
    from rest_framework.test import APIClient

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token_user["access"]}')
    return client