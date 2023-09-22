''' Main urls '''

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
   path('admin/', admin.site.urls),
   path('api/', include('users.urls')),
   path('api/', include('vocabulary.urls')),

   # Конфигурация DRF_Spectacular для просмотра документации
   path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
   path('api/schema/docs/',
      SpectacularSwaggerView.as_view(url_name='schema'))
]

if settings.DEBUG:
    urlpatterns += static(
      settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
