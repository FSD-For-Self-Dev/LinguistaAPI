"""Маршруты приложения words."""

from django.urls import path, include
from . import views
from rest_framework import routers
from .views import WordViewSet

router = routers.SimpleRouter()
router.register(r'word', WordViewSet, basename='word')

urlpatterns = [
    # path('words/', views.WordViewSet.as_view({'get': 'get_word'})),
    # path('random/', views.WordViewSet.as_view({'get': 'random'})),
    path('v1/', include(router.urls)),
]
