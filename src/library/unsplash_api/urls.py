"""Unsplash_api app urls."""

from django.urls import path

from .views import UnsplashImagesView

urlpatterns = [
    path(
        'unsplash/images/',
        UnsplashImagesView.as_view(),
        name='get-unsplash-images',
    ),
]
