''' Vocabulary views '''

import random

from django.contrib.auth import get_user_model
from django.db.models import Count

from django_filters.rest_framework import DjangoFilterBackend
# from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
# from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.pagination import LimitPagination
from vocabulary.models import Word

from .filters import WordFilter
from .serializers import TranslationSerializer, VocabularySerializer

User = get_user_model()


class WordViewSet(viewsets.ModelViewSet):
    '''Вьюсет для модели слова.'''

    # queryset = Word.objects.all()
    serializer_class = VocabularySerializer
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']
    permission_classes = [
        IsAuthenticated,
        # AllowAny,
    ]
    pagination_class = LimitPagination
    filter_backends = [
        filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    ]
    # filterset_class = WordFilter
    # search_fields = (
    #     'text', 'note', 'tags__name', 'translations__translation',
    #     'examples__example'
    # )
    # ordering_fields = (
    #     'created', 'modified', 'text', 'trnsl_count', 'exmpl_count'
    # )
    ordering = ('-created',)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.vocabulary.all().annotate(
                trnsl_count=Count('translations'),
                exmpl_count=Count('examples')
            )
        return None

    @action(methods=['get'], detail=False)
    def random(self, request, *args, **kwargs):
        '''Get random word from vocabulary'''
        queryset = self.filter_queryset(self.get_queryset())
        word = random.choice(queryset)
        serializer = VocabularySerializer(
            word, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get', 'post'], detail=True)
    def translations(self, request, *args, **kwargs):
        '''Get all word's translations or add new translation to word'''
        word = get_object_or_404(Word, pk=kwargs.get('pk'))
        translations = word.translations.all()
        serializer = TranslationSerializer(
            translations, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
