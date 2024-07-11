"""Exercises urls."""

from django.urls import include, path

from rest_framework import routers

from .views import ExerciseViewSet

router = routers.DefaultRouter()

router.register('exercises', ExerciseViewSet, basename='exercises')

urlpatterns = [
    path('', include(router.urls)),
]
