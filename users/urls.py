"""Users app urls."""

from django.urls import include, path

from rest_framework import routers

from .views import UserViewSet

router = routers.DefaultRouter()

router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('', include(router.urls)),
]
