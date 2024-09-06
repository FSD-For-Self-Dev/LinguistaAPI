"""Authentication custom views."""

from rest_framework.generics import RetrieveUpdateDestroyAPIView

from dj_rest_auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    UserDetailsView,
)
from dj_rest_auth.registration.views import (
    RegisterView,
    VerifyEmailView,
    ResendEmailVerificationView,
)

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


@extend_schema(tags=['authentication'])
@extend_schema_view(
    post=extend_schema(operation_id='auth_login'),
)
class CustomLoginView(LoginView):
    pass


@extend_schema(tags=['authentication'])
@extend_schema_view(
    post=extend_schema(operation_id='auth_logout'),
    get=extend_schema(operation_id='auth_logout'),
)
class CustomLogoutView(LogoutView):
    http_method_names = ('post',)
    pass


@extend_schema(tags=['authentication'])
@extend_schema_view(
    post=extend_schema(operation_id='auth_password_reset'),
)
class CustomPasswordResetView(PasswordResetView):
    pass


@extend_schema(tags=['authentication'])
@extend_schema_view(
    post=extend_schema(operation_id='auth_password_reset_confirm'),
)
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    pass


@extend_schema(tags=['authentication'])
@extend_schema_view(
    post=extend_schema(operation_id='auth_password_change'),
)
class CustomPasswordChangeView(PasswordChangeView):
    pass


@extend_schema(tags=['registration'])
@extend_schema_view(
    post=extend_schema(operation_id='auth_registration'),
)
class CustomRegisterView(RegisterView):
    pass


@extend_schema(tags=['registration'])
@extend_schema_view(
    post=extend_schema(operation_id='auth_registration_verify_email'),
)
class CustomVerifyEmailView(VerifyEmailView):
    pass


@extend_schema(tags=['registration'])
@extend_schema_view(
    post=extend_schema(operation_id='auth_registration_resend_email'),
)
class CustomResendEmailVerificationView(ResendEmailVerificationView):
    pass
