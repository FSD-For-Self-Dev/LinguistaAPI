"""Url patterns."""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('unsplash/', include('library.unsplash_api.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('browsable-auth/', include('rest_framework.urls', namespace='rest_framework')),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('api/', include('api.v1.urls')),
    # Save the prefix for the default language
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
