import random

from django.contrib.auth import get_user_model

# from djoser.views import UserViewSet
from rest_framework import status, viewsets  # filters
from rest_framework.decorators import action
# from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from words.models import Word

from .serializers import WordSerializer, TranslationSerializer

User = get_user_model()


class WordViewSet(viewsets.ModelViewSet):
    queryset = Word.objects.all()
    serializer_class = WordSerializer
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']
    permission_classes = [
        # IsAuthorOrReadOnly,
        AllowAny,
    ]
    # pagination_class = CursorSetPagination
    # filter_backends = (RQLFilterBackend, filters.OrderingFilter)
    # rql_filter_class = RecipeFilters
    # ordering_fields = ['created']
    # ordering = ('-created',)
    # filter_backends = [
    #     filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    # ]
    # filterset_class = RecipeFilter

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
