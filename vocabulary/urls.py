"""Маршруты приложения words."""

from django.urls import include, path
from rest_framework import routers

from .views import WordViewSet, CollectionViewSet

router = routers.DefaultRouter()

router.register('vocabulary', WordViewSet, basename='vocabulary')
router.register('collections', CollectionViewSet, basename='collections')
# router.register('tags', TagViewSet, basename='tags')
# router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
]
