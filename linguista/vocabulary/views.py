''' Vocabulary views '''

import random

from django.contrib.auth import get_user_model
from django.db.models import Count

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
# from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
# from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.pagination import LimitPagination
from vocabulary.models import Word

from .filters import WordFilter
from .models import Definition, WordDefinitions
from .serializers import (TranslationSerializer, VocabularySerializer,
                          DefinitionSerializer)

User = get_user_model()


@extend_schema(tags=['vocabulary'])
class WordViewSet(viewsets.ModelViewSet):
    '''Word model viewset'''

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
                exmpl_count=Count('wordusageexamples')
            )
        return None

    @action(methods=['get'], detail=False)
    def random(self, request, *args, **kwargs):
        '''Get random word from vocabulary'''
        queryset = self.filter_queryset(self.get_queryset())
        word = random.choice(queryset) if queryset else None
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


class DefinitionViewSet(viewsets.ViewSet):
    """Viewset for word definitions"""

    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']
    serializer_class = DefinitionSerializer

    def get_word_with_author(self):
        """Get word and its author or 404/403 with custom message"""

        word = Word.objects.filter(
            slug=self.kwargs.get('slug')
        ).select_related('author').first()
        if not word:
            raise NotFound(
                detail="The word with the provided slug not found",
            )
        elif word.author != self.request.user:
            raise PermissionDenied(
                detail='You are not the author of this word'
            )
        return word, word.author

    def get_obj(self):
        definition = get_object_or_404(
            Definition,
            pk=self.kwargs.get('pk'),
            worddefinitions__word__slug=self.kwargs.get('slug')
        )
        return definition

    def list(self, request, slug=None):
        """Get all definitions for a given word provided with a slug"""
        word, _ = self.get_word_with_author()
        queryset = word.definitions.all()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(examples=[OpenApiExample(
        'Default',
        value=[{'text': 'string', 'translation': 'string'}]
    )])
    def create(self, request, slug=None, many=True):
        """Create new definitions for a given word"""

        word, author = self.get_word_with_author()
        serializer = self.serializer_class(data=request.data, many=True)
        if serializer.is_valid():
            definitions = []
            word_definitions = []

            for definition in serializer.validated_data:
                _definition = Definition(**definition, author=author)
                definitions.append(_definition)
                word_definitions.append(
                    WordDefinitions(word=word, definition=_definition)
                )
            Definition.objects.bulk_create(definitions)
            WordDefinitions.objects.bulk_create(word_definitions)

            return Response(
                self.serializer_class(definitions, many=True).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(parameters=[
        OpenApiParameter("id", int, OpenApiParameter.PATH)
    ])
    def partial_update(self, request, slug=None, pk=None):
        """Partial update of a definition with PATCH request"""

        self.get_word_with_author()
        obj = self.get_obj()
        serializer = self.serializer_class(
            instance=obj,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(parameters=[
        OpenApiParameter("id", int, OpenApiParameter.PATH)
    ])
    def destroy(self, request, slug=None, pk=None):
        """Delete a definition"""

        self.get_word_with_author()
        obj = self.get_obj()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
