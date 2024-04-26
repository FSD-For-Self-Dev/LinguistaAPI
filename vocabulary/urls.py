"""Маршруты приложения words."""

from django.urls import include, path

from rest_framework import routers

from .views import (
    CollectionViewSet,
    FormsGroupsViewSet,
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
    LanguagesViewSet,
    MainPageViewSet,
)

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
router.register('forms-groups', FormsGroupsViewSet, basename='forms-groups')
router.register('images', ImageViewSet, basename='images')
router.register('quotes', QuoteViewSet, basename='quotes')
router.register('associations', AssociationViewSet, basename='associations')

router.register('collections', CollectionViewSet, basename='collections')

router.register('languages', LanguagesViewSet, basename='languages')

router.register('main', MainPageViewSet, basename='main')

urlpatterns = [
    path('', include(router.urls)),
]
