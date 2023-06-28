from django.urls import include, path

from rest_framework import routers

from .views import WordViewSet

router = routers.DefaultRouter()

router.register('recipes', WordViewSet, basename='words')
# router.register('tags', TagViewSet, basename='tags')
# router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    # path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
