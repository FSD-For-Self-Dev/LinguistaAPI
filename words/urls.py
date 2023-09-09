"""Маршруты приложения words."""

from django.urls import include, path

from rest_framework import routers

from . import views
from .views import WordViewSet

# router = routers.DefaultRouter()
#
# router.register('words', WordViewSet, basename='words')
# router.register('tags', TagViewSet, basename='tags')
# router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('words/', views.WordViewSet.as_view({'get': 'get_word'})),
]
