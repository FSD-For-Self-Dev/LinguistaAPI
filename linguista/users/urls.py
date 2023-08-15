"""Маршруты приложения users."""

from django.urls import include, path
from rest_framework import routers

from .views import UserViewSet

router = routers.DefaultRouter()

router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls.jwt')),
    path('', include(router.urls)),
]
