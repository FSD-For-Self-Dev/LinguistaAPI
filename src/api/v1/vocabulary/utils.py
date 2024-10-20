"""Vocabulary app utils."""

import logging

from django.http import HttpRequest

from rest_framework.serializers import Serializer

from apps.vocabulary.models import DefaultWordCards

from .serializers import (
    WordStandartCardSerializer,
    WordShortCardSerializer,
    WordLongCardSerializer,
)

logger = logging.getLogger(__name__)

WORD_CARD_TYPES = {
    'standart': WordStandartCardSerializer,
    'short': WordShortCardSerializer,
    'long': WordLongCardSerializer,
}
DEFAULT_WORD_CARD_TYPE = 'standart'


def get_word_cards_type(request: HttpRequest) -> Serializer:
    """Returns serializer class for words list."""

    # Return serializer class based on `cards_type` query parameter if passed
    # or try to get user default word cards type setting from database
    # or return serializer class defined in types for `default_type`.
    type_param = request.query_params.get('cards_type', None)
    logger.debug(f'Word cards view query parameter passed: {type_param}')

    if type_param:
        return WORD_CARD_TYPES.get(
            type_param, WORD_CARD_TYPES.get(DEFAULT_WORD_CARD_TYPE)
        )

    try:
        user_default_type = DefaultWordCards.objects.get(user=request.user).cards_type
        logger.debug(
            f'Word cards type obtained from users default settings: '
            f'{user_default_type}'
        )
    except Exception:
        user_default_type = DEFAULT_WORD_CARD_TYPE
        logger.debug(
            f'Word cards type parameter is set to default: {DEFAULT_WORD_CARD_TYPE}'
        )

    return WORD_CARD_TYPES.get(user_default_type)
