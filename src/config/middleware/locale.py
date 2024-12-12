"""Custom locale middleware."""
from django.http.response import HttpResponseRedirectBase
from django.middleware.locale import LocaleMiddleware as DjangoLocaleMiddleware


class HttpResponseTemporaryRedirect(HttpResponseRedirectBase):
    """Custom class to server response with 307 status code."""

    status_code = 307


class LocaleMiddleware(DjangoLocaleMiddleware):
    """Custom locale middleware to allow unsave methods passing within redirect."""

    response_redirect_class = HttpResponseTemporaryRedirect
