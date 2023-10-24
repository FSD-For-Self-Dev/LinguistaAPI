"""Маршруты приложения words."""

from django.urls import include, path
from rest_framework import routers

from .views import WordViewSet, TypeViewSet, CollectionViewSet

router = routers.DefaultRouter()

router.register('vocabulary', WordViewSet, basename='vocabulary')
router.register('types', TypeViewSet, basename='types')
router.register('collections', CollectionViewSet, basename='collections')

urlpatterns = [
    path('', include(router.urls)),
]
