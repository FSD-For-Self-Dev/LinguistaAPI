"""View-функции приложения words."""

import random

from django.contrib.auth import get_user_model

from rest_framework import status, viewsets, pagination
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Word
from .serializers import TranslationSerializer, WordSerializer

User = get_user_model()


class WordViewSetPagination(pagination.PageNumberPagination):

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'current_page': int(self.request.query_params.get('page', 1)),
            'total': self.page.paginator.count,
            'per_page': self.page_size,
            'total_pages': round(self.page.paginator.count / self.page_size, 1),
            'data': data,
        })


class WordViewSet(viewsets.ModelViewSet):
    """Вьюсет для модели слова."""
    # queryset = Word.objects.all()
    serializer_class = WordSerializer
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']
    permission_classes = [IsAuthenticated]
    pagination_class = WordViewSetPagination

    @action(methods=['get'], detail=False)
    def get_word(self, request):
        # Get vocabilary list
        author_id = self.request.user
        queryset = Word.objects.prefetch_related('tags'). \
            filter(author=author_id)
        paginator = WordViewSetPagination()
        page_size = 2
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = WordSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(methods=['get'], detail=False)
    def random(self, request, *args, **kwargs):
        '''Get random word from vocabulary'''
        author_id = self.request.user
        queryset = Word.objects.prefetch_related('tags').filter(author=author_id)
        word = random.choice(queryset)
        serializer = WordSerializer(
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
