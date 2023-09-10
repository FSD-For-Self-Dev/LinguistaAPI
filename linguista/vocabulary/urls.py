''' Vocabulary urls '''

from django.urls import include, path

from rest_framework import routers

from .views import WordViewSet, DefinitionViewSet


VOCABULARY_PREFIX = 'vocabulary'

router = routers.DefaultRouter()
definition_router = routers.DefaultRouter()

router.register(VOCABULARY_PREFIX, WordViewSet, basename=VOCABULARY_PREFIX)
definition_router.register('definitions', DefinitionViewSet, basename='definitions')
# router.register('tags', TagViewSet, basename='tags')
# router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path(f'{VOCABULARY_PREFIX}/<slug:slug>/', include(definition_router.urls)),
    #path('', include(router.urls)),
]
