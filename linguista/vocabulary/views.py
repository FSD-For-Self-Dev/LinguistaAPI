''' Vocabulary views '''

import random

from django.contrib.auth import get_user_model
from django.db.models import Count

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
# from djoser.views import UserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.pagination import LimitPagination

# from vocabulary.models import Word
# from .filters import WordFilter
from .models import Definition, WordDefinitions
from .serializers import (TranslationSerializer, WordSerializer,
                          DefinitionSerializer)
from .permissions import CanAddDefinitionPermission

User = get_user_model()


@extend_schema(tags=['vocabulary'])
class WordViewSet(viewsets.ModelViewSet):
    '''Viewset for actions with words in user vocabulary'''

    lookup_field = 'slug'
    serializer_class = WordSerializer
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
