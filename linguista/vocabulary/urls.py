''' Vocabulary urls '''

from django.urls import include, path

from rest_framework import routers

from .views import WordViewSet, views


router = routers.DefaultRouter()

router.register('vocabulary', WordViewSet, basename='vocabulary')
# router.register('tags', TagViewSet, basename='tags')
# router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('bulk_add_words/', views.bulk_add_words, name='bulk_add_words'),
]
