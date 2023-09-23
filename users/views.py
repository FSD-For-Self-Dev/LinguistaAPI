''' Users views '''

# from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets

from .serializers import UserSerializer

# from .filters import UserFilter

User = get_user_model()


@extend_schema(tags=['users'])
class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    '''Список пользователей'''

    serializer_class = UserSerializer

    def get_queryset(self):
        """Исключение админов из выборки."""
        return User.objects.filter(is_staff=False)
