"""View-функции приложения words."""

import random

from django.contrib.auth import get_user_model
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import filters, status, viewsets, pagination
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from words.models import Word

from .filters import WordFilter
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

    queryset = Word.objects.all()
    serializer_class = WordSerializer
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']
    permission_classes = [
        IsAuthenticated,
    ]

    filter_backends = [
        filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    ]
    filterset_class = WordFilter
    search_fields = (
        'text', 'note', 'tags__name', 'translations__translation',
        'examples__example'
    )
    ordering_fields = (
        'created', 'modified', 'text', 'trnsl_count', 'exmpl_count'
    )
    ordering = ('-created',)

    def get_word(self, request):
        # Get vocabilary list
        try:
            author_id = self.request.user
            #queryset = Word.objects.filter(author=author_id)
            queryset = Word.objects.prefetch_related('tags').filter(author=author_id)

        except Word.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'GET':
            if request.user.is_authenticated:
                paginator = WordViewSetPagination()
                page_size = 78
                paginator.page_size = page_size
                result_page = paginator.paginate_queryset(queryset, request)
                serializer = WordSerializer(result_page, many=True)
                # return Response(serializer.data)
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.words.all().annotate(
                trnsl_count=Count('translations'),
                exmpl_count=Count('examples')
            )
        return None

    @action(methods=['get'], detail=False)
    def random(self, request, *args, **kwargs):
        '''Get random word from vocabulary'''
        queryset = self.filter_queryset(self.get_queryset())
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
