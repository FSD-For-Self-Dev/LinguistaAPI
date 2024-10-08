"""Authorization url Zpatterns"""

from django.urls import path
from allauth.account.views import ConfirmEmailView

from .views import (
    UserDetailsWithDestroyView,
    CustomLoginView,
    CustomLogoutView,
    CustomPasswordResetView,
    CustomPasswordResetConfirmView,
    CustomPasswordChangeView,
    CustomRegisterView,
    CustomResendEmailVerificationView,
    CustomVerifyEmailView,
)


urlpatterns = [
    # URLs that do not require a session or valid token
    path('login/', CustomLoginView.as_view(), name='login'),
    path(
        'password/reset/',
        CustomPasswordResetView.as_view(),
        name='password_reset',
    ),
    path(
        'password/reset/confirm/<str:uidb64>/<str:token>/',
        CustomPasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path('registration/', CustomRegisterView.as_view(), name='register'),
    path(
        'registration/account-confirm-email/<str:key>/',
        ConfirmEmailView.as_view(),
        name='account_confirm_email',
    ),
    path(
        'registration/verify-email/',
        CustomVerifyEmailView.as_view(),
        name='account_email_verification_sent',
    ),
    path(
        'registration/resend-email/',
        CustomResendEmailVerificationView.as_view(),
        name='resend_email',
    ),
    # URLs that require a user to be logged in with a valid session / token.
    path(
        'password/change/',
        CustomPasswordChangeView.as_view(),
        name='password_change',
    ),
    path('user/', UserDetailsWithDestroyView.as_view(), name='user_details'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
]
