"""API url patterns."""

from django.urls import include, path

from rest_framework import routers
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from .vocabulary.views import (
    CollectionViewSet,
    FormGroupsViewSet,
    TypeViewSet,
    WordViewSet,
    DefinitionViewSet,
    UsageExampleViewSet,
    WordTranslationViewSet,
    TagViewSet,
    SynonymViewSet,
    AntonymViewSet,
    SimilarViewSet,
    ImageViewSet,
    QuoteViewSet,
    AssociationViewSet,
    MainPageViewSet,
)
from .users.views import UserViewSet
from .exercises.views import ExerciseViewSet
from .languages.views import LanguageViewSet

router = routers.DefaultRouter()

router.register('vocabulary', WordViewSet, basename='vocabulary')

router.register('translations', WordTranslationViewSet, basename='translations')
router.register('definitions', DefinitionViewSet, basename='definitions')
router.register('examples', UsageExampleViewSet, basename='examples')
router.register('synonyms', SynonymViewSet, basename='synonyms')
router.register('antonyms', AntonymViewSet, basename='antonyms')
router.register('similars', SimilarViewSet, basename='similars')
router.register('tags', TagViewSet, basename='tags')
router.register('types', TypeViewSet, basename='types')
router.register('forms-groups', FormGroupsViewSet, basename='forms-groups')
router.register('images', ImageViewSet, basename='images')
router.register('quotes', QuoteViewSet, basename='quotes')
router.register('associations', AssociationViewSet, basename='associations')

router.register('collections', CollectionViewSet, basename='collections')

router.register('languages', LanguageViewSet, basename='languages')

router.register('main', MainPageViewSet, basename='main')

router.register('users', UserViewSet, basename='users')

router.register('exercises', ExerciseViewSet, basename='exercises')

urlpatterns = [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'schema/swagger-ui/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'schema/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
    path('auth/', include('api.v1.auth.urls')),
    path('', include(router.urls)),
]
