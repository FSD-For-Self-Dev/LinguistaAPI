"""Users schema data."""

from rest_framework import status


from api.v1.users.serializers import (
    UserListSerializer,
)


data = {
    'UserViewSet': {
        'tags': ['users'],
        'users_list': {
            'summary': 'Просмотр списка пользователей',
            'request': None,
            'responses': {
                status.HTTP_200_OK: UserListSerializer,
            },
        },
        # other methods
    },
}
