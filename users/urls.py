"""Users app urls."""

from django.urls import include, path

from rest_framework import routers

from dj_rest_auth.registration.views import ConfirmEmailView

from .views import UserViewSet, UserDetailsWithDestroyView

router = routers.DefaultRouter()

router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path(
        'auth/registration/account-confirm-email/<str:key>/',
        ConfirmEmailView.as_view(),
        name='email-confirmation',
    ),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/user/', UserDetailsWithDestroyView.as_view(), name='user_details'),
    path('auth/', include('dj_rest_auth.urls')),
    path('', include(router.urls)),
]
