from django.utils.version import get_version

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def api_client():
    return APIClient

def auth_client(user):
    refresh = RefreshToken.for_user(user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return client


assert get_version() <= '4.2.2', 'Пожалуйста, используйте версию Django <= 4.2.2'

# pytest_plugins = [
#     'tests.fixtures.fixture_user',
# ]
