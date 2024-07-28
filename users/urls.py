"""Users app urls."""

from django.urls import include, path

from rest_framework import routers

from dj_rest_auth.registration.views import VerifyEmailView, ConfirmEmailView

from .views import UserViewSet, UserDetailsWithDestroyView

router = routers.DefaultRouter()

router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/user/', UserDetailsWithDestroyView.as_view(), name='rest_user_details'),
    path(
        'auth/registration/account-confirm-email/<str:key>/',
        ConfirmEmailView.as_view(),
    ),
    path(
        'dj-rest-auth/account-confirm-email/',
        VerifyEmailView.as_view(),
        name='account_email_verification_sent',
    ),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/', include('dj_rest_auth.urls')),
    path('', include(router.urls)),
]
