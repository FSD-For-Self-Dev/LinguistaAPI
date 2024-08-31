"""Authentication custom views."""

from rest_framework.generics import RetrieveUpdateDestroyAPIView

from dj_rest_auth.views import UserDetailsView
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)


@extend_schema(tags=['user_profile'])
@extend_schema_view(
    get=extend_schema(operation_id='user_retrieve'),
    put=extend_schema(operation_id='user_update'),
    patch=extend_schema(operation_id='user_partial_update'),
    delete=extend_schema(operation_id='user_destroy'),
)
class UserDetailsWithDestroyView(UserDetailsView, RetrieveUpdateDestroyAPIView):
    """Add destroy action to user detail actions."""
