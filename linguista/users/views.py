""" Users views """

# from django_filters.rest_framework import DjangoFilterBackend
# from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model

from djoser.views import UserViewSet as DjoserViewSet

# from .filters import UserFilter

User = get_user_model()

# @extend_schema(tags=['Users'])
class UserViewSet(DjoserViewSet):
    """Вьюсет модели пользователя."""
    
    ...
