"""Маршруты приложения users."""

from django.urls import include, path, re_path
from rest_framework import routers

from .views import UserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


router = routers.DefaultRouter()

router.register('users', UserViewSet, basename='users')

urlpatterns = [
    #авторизация. добавить users
    path('auth/', include('djoser.urls')),
    #аутентификация. дописать login или logout
    path('user_auth/', include('rest_framework.urls')),
    #получение токена. дописать token/login
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
