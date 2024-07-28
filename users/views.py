"""Users views."""

from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveUpdateDestroyAPIView

from dj_rest_auth.views import UserDetailsView

from core.pagination import LimitPagination

from .serializers import UserShortSerializer

User = get_user_model()


@extend_schema(tags=['users'])
@extend_schema_view(
    list=extend_schema(operation_id='users_list'),
)
class UserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """List users."""

    http_method_names = ('get',)
    queryset = User.objects.none()
    serializer_class = UserShortSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination

    def get_queryset(self) -> QuerySet:
        """Exclude admins from users list."""
        return User.objects.filter(is_staff=False)


class UserDetailsWithDestroyView(UserDetailsView, RetrieveUpdateDestroyAPIView):
    """Add destroy action to user detail actions."""
