from django.urls import include, path

from rest_framework import routers
from rest_framework.authtoken import views

from .views import WordViewSet

router = routers.DefaultRouter()

router.register('words', WordViewSet, basename='words')
# router.register('tags', TagViewSet, basename='tags')
# router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    # path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('api-token-auth/', views.obtain_auth_token),
]
