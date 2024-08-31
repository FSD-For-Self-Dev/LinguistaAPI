"""Authorization url patterns"""

from django.urls import include, path
from dj_rest_auth.registration.views import ConfirmEmailView


urlpatterns = [
    path(
        'registration/account-confirm-email/<str:key>/',
        ConfirmEmailView.as_view(),
        name='email-confirmation',
    ),
    path('registration/', include('dj_rest_auth.registration.urls')),
    path('', include('dj_rest_auth.urls')),
]
