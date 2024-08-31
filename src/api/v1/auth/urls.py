"""Authorization url Zpatterns"""

from django.urls import include, path
from dj_rest_auth.registration.views import ConfirmEmailView

from .views import UserDetailsWithDestroyView


urlpatterns = [
    path(
        'registration/account-confirm-email/<str:key>/',
        ConfirmEmailView.as_view(),
        name='email-confirmation',
    ),
    path('registration/', include('dj_rest_auth.registration.urls')),
    path('user/', UserDetailsWithDestroyView.as_view(), name='user_details'),
    path('', include('dj_rest_auth.urls')),
]
