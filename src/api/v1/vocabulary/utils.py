"""Vocabulary app utils."""

import logging

from django.db.models import Count, Model
from django.db.models.query import QuerySet
from django.http import HttpRequest

from rest_framework.serializers import Serializer

from apps.vocabulary.models import DefaultWordCards, Word

from .serializers import (
    WordStandartCardSerializer,
    WordShortCardSerializer,
    WordLongCardSerializer,
)

logger = logging.getLogger(__name__)


def get_word_cards_type(request: HttpRequest) -> Serializer:
    """Returns serializer class for words list."""
    types = {
        'standart': WordStandartCardSerializer,
        'short': WordShortCardSerializer,
        'long': WordLongCardSerializer,
    }
    default_type = 'standart'

    # Return serializer class based on `cards_type` query parameter if passed
    # or try to get user default word cards type setting from database
    # or return serializer class defined in types for `default_type`.
    type_param = request.query_params.get('cards_type', None)
    logger.debug(f'Word cards view query parameter passed: {type_param}')

    if type_param:
        return types.get(type_param, types.get(default_type))

    try:
        user_default_type = DefaultWordCards.objects.get(user=request.user).cards_type
        logger.debug(
            f'Word cards type obtained from users default settings: '
            f'{user_default_type}'
        )
    except Exception:
        user_default_type = default_type
        logger.debug(f'Word cards type parameter is set to default: {default_type}')

    return types.get(user_default_type)


def annotate_words_with_counters(
    words: QuerySet[Word] | None = None,
    instance: Model | None = None,
    words_related_name: str = '',
    ordering: list[str] = [],
) -> QuerySet[Word]:
    """
    Annotates words with some related objects amount to use in filters, sorting.

    Args:
        words (QuerySet): words queryset to be annotated.
        instance (Model subclass): instance to obtain words from if words not passed.
        words_related_name (str): related name to obtain words by if words not passed.
        ordering (list[str]): list of fields to be sorted words by.
    """
    if words is None:
        return (
            instance.__getattribute__(words_related_name)
            .annotate(
                translations_count=Count('translations', distinct=True),
                examples_count=Count('examples', distinct=True),
                collections_count=Count('collections', distinct=True),
            )
            .order_by(*ordering)
        )

    return words.annotate(
        translations_count=Count('translations', distinct=True),
        examples_count=Count('examples', distinct=True),
        collections_count=Count('collections', distinct=True),
    ).order_by(*ordering)
