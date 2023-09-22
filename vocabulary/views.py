''' Vocabulary views '''

import random

from django.contrib.auth import get_user_model
from django.db.models import Count

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   extend_schema)
# from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.pagination import LimitPagination

# from .filters import WordFilte
from .models import (Definition, UsageExample, WordDefinitions,
                     WordUsageExamples)
from .permissions import (CanAddDefinitionPermission,
                          CanAddUsageExamplePermission)
from .serializers import (DefinitionSerializer, TranslationSerializer,
                          UsageExampleSerializer, WordListSerializer,
                          WordSerializer)

User = get_user_model()


@extend_schema(tags=['vocabulary'])
class WordViewSet(viewsets.ModelViewSet):
    '''Viewset for actions with words in user vocabulary'''

    lookup_field = 'slug'
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']
    permission_classes = [IsAuthenticated]
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
        '''
        Get all words from user's vocabulary with counted translations 
        & usage examples
        '''
        user = self.request.user
        if user.is_authenticated:
            return user.vocabulary.annotate(
                translations_count=Count('translations', distinct=True),
                examples_count=Count('examples', distinct=True)
            )
        return None

    def get_serializer_class(self):
        match self.action:
            case 'list':
                return WordListSerializer
            case _:
                return WordSerializer

    @action(methods=['get'], detail=False)
    def random(self, request, *args, **kwargs):
        '''Get random word from vocabulary'''
        queryset = self.filter_queryset(self.get_queryset())
        word = random.choice(queryset) if queryset else None
        serializer = WordSerializer(
            word, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=TranslationSerializer
    )
    def translations(self, request, *args, **kwargs):
        '''Get all word's translations or add new translation to word'''
        word = self.get_object()
        translations = word.translations.all()
        serializer = TranslationSerializer(
            translations, many=True, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=DefinitionSerializer,
        permission_classes=[IsAuthenticated, CanAddDefinitionPermission]
    )
    def definitions(self, request, *args, **kwargs):
        """Get all definitions to a word or add new definition"""
        word = self.get_object()
        defs = word.definitions.all()

        match request.method:
            case "GET":
                return Response(
                    self.get_serializer(defs, many=True).data,
                    status=status.HTTP_200_OK
                )
            case "POST":
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                new_def = serializer.save(
                    author=request.user,
                    **serializer.validated_data
                )
                WordDefinitions.objects.create(definition=new_def, word=word)
                return Response(self.get_serializer(new_def).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['get', 'patch', 'delete'],
        url_path=r'definitions/(?P<definition_id>\d+)',
        url_name="word's definition detail",
        serializer_class=DefinitionSerializer,
    )
    def definitions_detail(self, request, *args, **kwargs):
        """Retrieve, update or delete a word definition"""
        word = self.get_object()
        try:
            definition = word.definitions.get(pk=kwargs.get('definition_id'))
        except Definition.DoesNotExist:
            raise NotFound(detail="The definition not found")

        match request.method:
            case 'GET':
                return Response(self.get_serializer(definition).data)
            case 'PATCH':
                serializer = self.get_serializer(
                    instance=definition,
                    data=request.data,
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            case 'DELETE':
                definition.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=UsageExampleSerializer,
        permission_classes=[IsAuthenticated, CanAddUsageExamplePermission]
    )
    def examples(self, request, *args, **kwargs):
        """Get all usage examples of a word or add new usage example"""
        word = self.get_object()
        _examples = word.examples.all()
        match request.method:
            case "GET":
                return Response(
                    self.get_serializer(_examples, many=True).data,
                    status=status.HTTP_200_OK
                )
            case "POST":
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                new_example = serializer.save(
                    author=request.user,
                    **serializer.validated_data
                )
                WordUsageExamples.objects.create(example=new_example, word=word)
                return Response(self.get_serializer(new_example).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['get', 'patch', 'delete'],
        url_path=r'examples/(?P<example_id>\d+)',
        url_name="word's usage example detail",
        serializer_class=UsageExampleSerializer,
    )
    def examples_detail(self, request, *args, **kwargs):
        """Retrieve, update or delete a word usage example"""
        word = self.get_object()
        try:
            _example = word.examples.get(pk=kwargs.get('example_id'))
        except UsageExample.DoesNotExist:
            raise NotFound(detail="The usage example not found")
        match request.method:
            case 'GET':
                return Response(self.get_serializer(_example).data)
            case 'PATCH':
                serializer = self.get_serializer(
                    instance=_example,
                    data=request.data,
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            case 'DELETE':
                _example.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
