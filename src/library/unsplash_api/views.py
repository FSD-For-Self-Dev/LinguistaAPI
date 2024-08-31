"""Unsplash_api app views."""

import os
import requests
import logging

from django.http import HttpRequest, HttpResponse

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from core.exceptions import ServiceUnavailable

from .constants import MAIN_URL

logger = logging.getLogger(__name__)


class UnsplashImagesView(GenericAPIView):
    """Actions with images from Unsplash API."""

    http_method_names = ('get', 'options')
    permission_classes = (AllowAny,)

    all_images_list_url = MAIN_URL + 'photos/'
    search_images_url = MAIN_URL + 'search/photos/'
    default_per_page_value = 20

    @staticmethod
    def get_headers() -> dict[str, str]:
        """Returns dictionary of request headers."""
        client_id = os.getenv('UNSPLASH_CLIENT_ID', default='')

        return {
            'Accept-Version': 'v1',
            'Authorization': f'Client-ID {client_id}',
        }

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of images returned by Unsplash API."""
        url = self.all_images_list_url
        headers = self.get_headers()

        # switch url if search param passed
        search_value: str = request.query_params.get('search', '')
        if search_value:
            url = self.search_images_url

        # set default per page value if per_page param not passed
        per_page_value: int = request.query_params.get(
            'per_page', self.default_per_page_value
        )

        # raise ServiceUnavailable custom exception if Unsplash service is unreachable
        try:
            response = requests.get(
                url,
                headers=headers,
                params={
                    'query': search_value,
                    'per_page': per_page_value,
                    **request.query_params,
                },
            )
        except Exception as exception:
            logger.error(
                f'ServiceUnavailable exception is raised, reason is: {exception}'
            )
            raise ServiceUnavailable

        return Response(response.json())
