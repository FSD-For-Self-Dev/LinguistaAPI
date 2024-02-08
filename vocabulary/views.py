"""Обработчики приложения vocabulary."""

import random

from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.pagination import LimitPagination

from .constants import MAX_EXAMPLES_AMOUNT
from .filters import CollectionFilter, WordFilter
from .models import (
    Collection,
    Definition,
    FavoriteCollection,
    FormsGroup,
    Type,
    UsageExample,
    WordDefinitions,
    WordTranslation,
    WordTranslations,
    WordUsageExamples,
    Word,
    Synonym, Similar,
)
from .permissions import (
    CanAddDefinitionPermission,
    CanAddUsageExamplePermission,
    IsAuthorOrReadOnly,
)
from .serializers import (
    CollectionSerializer,
    CollectionShortSerializer,
    CollectionsListSerializer,
    DefinitionSerializer,
    FormsGroupSerializer,
    TranslationSerializer,
    TypeSerializer,
    UsageExampleSerializer,
    WordSerializer,
    WordShortSerializer,
    SynonymSerializer, SimilarSerializer,
)

User = get_user_model()


@extend_schema_view(
    list=extend_schema(operation_id='words_list'),
    create=extend_schema(operation_id='word_create'),
    retrieve=extend_schema(operation_id='word_retrieve'),
    partial_update=extend_schema(operation_id='word_partial_update'),
    destroy=extend_schema(operation_id='word_destroy'),
)
class WordViewSet(viewsets.ModelViewSet):
    """Действия со словами из своего словаря."""

    lookup_field = 'slug'
    http_method_names = ('get', 'post', 'head', 'patch', 'delete')
    permission_classes = (IsAuthenticated,)
    queryset = Word.objects.none()
    pagination_class = LimitPagination
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    )
    filterset_class = WordFilter
    ordering = ('-created',)
    ordering_fields = ('created', 'text', 'translations_count')
    search_fields = (
        'text',
        'translations__text',
        'tags__name',
        'definitions__text',
        'definitions__translation',
    )

    def get_queryset(self):
        """
        Получить все слова из словаря пользователя с вычисленным кол-вом
        переводов и примеров использования.
        """
        user = self.request.user
        if user.is_authenticated:
            return user.vocabulary.annotate(
                translations_count=Count('translations', distinct=True),
                examples_count=Count('examples', distinct=True),
                collections_count=Count('collections', distinct=True),
            )
        return None

    def get_serializer_class(self):
        match self.action:
            case 'list' | 'random':
                return WordShortSerializer
            case 'translations' | 'translations_detail':
                return TranslationSerializer
            case 'definitions' | 'definitions_detail':
                return DefinitionSerializer
            case 'examples' | 'examples_detail':
                return UsageExampleSerializer
            case 'synonyms' | 'synonyms_detail':
                return SynonymSerializer
            case _:
                return WordSerializer

    @extend_schema(operation_id='word_random')
    @action(methods=['get'], detail=False)
    def random(self, request, *args, **kwargs):
        """Получить случайное слово из словаря."""
        queryset = self.filter_queryset(self.get_queryset())
        word = random.choice(queryset) if queryset else None
        serializer = self.get_serializer(word, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(operation_id='translations_list', methods=['get'])
    @extend_schema(operation_id='translation_create', methods=['post'])
    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=TranslationSerializer,
        permission_classes=[IsAuthenticated],
    )
    def translations(self, request, *args, **kwargs):
        """Получить все переводы слова или добавить новый перевод."""
        word = self.get_object()
        translations = word.translations.all()

        match request.method:
            case 'GET':
                serializer = TranslationSerializer(
                    translations, many=True, context={'request': request}
                )
                return Response(serializer.data, status=status.HTTP_200_OK)

            case 'POST':
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                new_translation = serializer.save(author_id=request.user.id)

                WordTranslations.objects.create(translation=new_translation, word=word)
                return Response(
                    self.get_serializer(new_translation).data,
                    status=status.HTTP_201_CREATED,
                )

    @extend_schema(operation_id='translations_retrieve', methods=['get'])
    @extend_schema(operation_id='translation_partial_update', methods=['patch'])
    @extend_schema(operation_id='translation_destroy', methods=['delete'])
    @action(
        detail=True,
        methods=['patch', 'delete'],
        url_path=r'translations/(?P<translation_id>\d+)',
        url_name="word's translations detail",
        serializer_class=TranslationSerializer,
    )
    def translations_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить перевод слова."""
        word = self.get_object()
        try:
            translation = word.translations.get(pk=kwargs.get('translation_id'))
        except WordTranslation.DoesNotExist:
            raise NotFound(detail='The translation not found')

        match request.method:
            case 'PATCH':
                serializer = self.get_serializer(
                    instance=translation, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            case 'DELETE':
                translation.delete()
                translations = word.translations.all()
                serializer = TranslationSerializer(
                    translations, many=True, context={'request': request}
                )
                return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(operation_id='definitions_list', methods=['get'])
    @extend_schema(operation_id='definition_create', methods=['post'])
    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=DefinitionSerializer,
        permission_classes=[IsAuthenticated, CanAddDefinitionPermission],
    )
    def definitions(self, request, *args, **kwargs):
        """Получить все определения слова или добавить новое определение."""
        word = self.get_object()
        defs = word.definitions.all()

        match request.method:
            case 'GET':
                return Response(
                    self.get_serializer(defs, many=True).data, status=status.HTTP_200_OK
                )
            case 'POST':
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                new_def = serializer.save(**serializer.validated_data)
                WordDefinitions.objects.create(definition=new_def, word=word)
                return Response(
                    self.get_serializer(new_def).data, status=status.HTTP_201_CREATED
                )

    @extend_schema(operation_id='definition_retrieve', methods=['get'])
    @extend_schema(operation_id='definition_partial_update', methods=['patch'])
    @extend_schema(operation_id='definition_destroy', methods=['delete'])
    @action(
        detail=True,
        methods=['get', 'patch', 'delete'],
        url_path=r'definitions/(?P<definition_id>\d+)',
        url_name="word's definition detail",
        serializer_class=DefinitionSerializer,
    )
    def definitions_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить определение слова."""
        word = self.get_object()
        try:
            definition = word.definitions.get(pk=kwargs.get('definition_id'))
        except Definition.DoesNotExist:
            raise NotFound(detail='The definition not found')

        match request.method:
            case 'GET':
                return Response(self.get_serializer(definition).data)
            case 'PATCH':
                serializer = self.get_serializer(
                    instance=definition, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            case 'DELETE':
                definition.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(operation_id='examples_list', methods=['get'])
    @extend_schema(operation_id='example_create', methods=['post'])
    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=UsageExampleSerializer,
        permission_classes=[IsAuthenticated, CanAddUsageExamplePermission],
    )
    def examples(self, request, *args, **kwargs):
        """Получить все примеры слова или добавить новый пример."""
        word = self.get_object()
        _examples = word.examples.all()
        match request.method:
            case 'GET':
                return Response(
                    self.get_serializer(_examples, many=True).data,
                    status=status.HTTP_200_OK,
                )
            case 'POST':
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                amount = len(_examples)
                if amount >= MAX_EXAMPLES_AMOUNT:
                    return Response(
                        {
                            'detail': _(
                                f'The maximum amount of examples ({amount}) '
                                'has already been reached.'
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                new_example = serializer.save(**serializer.validated_data)
                WordUsageExamples.objects.create(example=new_example, word=word)
                return Response(
                    self.get_serializer(new_example).data,
                    status=status.HTTP_201_CREATED,
                )

    @extend_schema(operation_id='example_retrieve', methods=['get'])
    @extend_schema(operation_id='example_partial_update', methods=['patch'])
    @extend_schema(operation_id='example_destroy', methods=['delete'])
    @action(
        detail=True,
        methods=['get', 'patch', 'delete'],
        url_path=r'examples/(?P<example_id>\d+)',
        url_name="word's usage example detail",
        serializer_class=UsageExampleSerializer,
    )
    def examples_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить пример использования слова."""
        word = self.get_object()
        try:
            _example = word.examples.get(pk=kwargs.get('example_id'))
        except UsageExample.DoesNotExist:
            raise NotFound(detail='The usage example not found')
        match request.method:
            case 'GET':
                return Response(self.get_serializer(_example).data)
            case 'PATCH':
                serializer = self.get_serializer(
                    instance=_example, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            case 'DELETE':
                _example.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(operation_id='problematic_toggle')
    @action(
        detail=True,
        methods=['post'],
        url_path='problematic-toggle',
        serializer_class=WordShortSerializer,
    )
    def problematic(self, request, *args, **kwargs):
        """Изменить значение метки is_problematic слова."""
        word = self.get_object()
        word.is_problematic = not word.is_problematic
        word.save()
        return Response(self.get_serializer(word).data)

    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=SynonymSerializer,
        permission_classes=[IsAuthenticated],
    )
    def synonyms(self, request, *args, **kwargs):
        """Получить все синонимы слова или добавить новый синоним."""
        word = self.get_object()
        synonyms = word.synonym_to_words.all()

        match request.method:
            case 'GET':
                serializer = SynonymSerializer(synonyms, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)

            case 'POST':
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                try:
                    serializer.save(author_id=request.user.id)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except IntegrityError:
                    return Response(
                        {'detail': 'Такой синоним уже существует.'},
                        status=status.HTTP_409_CONFLICT,
                    )

    @action(
        detail=True,
        methods=['patch', 'delete'],
        url_path=r'synonyms/(?P<synonym_id>\d+)',
        url_name="word's synonyms detail",
        serializer_class=SynonymSerializer,
    )
    def synonyms_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить синоним слова."""
        word = self.get_object()
        try:
            synonym = Synonym.objects.get(pk=kwargs.get('synonym_id'))
        except Synonym.DoesNotExist:
            raise NotFound(detail='The synonym not found')

        match request.method:
            case 'PATCH':
                serializer = self.get_serializer(
                    instance=synonym, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            case 'DELETE':
                synonym.delete()
                synonyms = Synonym.objects.filter(to_word=word)
                serializer = SynonymSerializer(
                    synonyms, many=True, context={'request': request}
                )
                return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['post'],
        detail=True,
        serializer_class=SimilarSerializer,
        permission_classes=[IsAuthenticated],
    )
    def similars(self, request, *args, **kwargs):
        """Добавить похожие слова."""
        match request.method:
            case 'POST':
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                try:
                    serializer.save(author_id=request.user.id)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except IntegrityError:
                    return Response(
                        {'detail': 'Такое слово уже добавлено.'},
                        status=status.HTTP_409_CONFLICT,
                    )

    @action(
        detail=True,
        methods=['delete'],
        url_path=r'similars/(?P<similar_id>\d+)',
        url_name="word's similars detail",
        serializer_class=SimilarSerializer,
    )
    def similars_delete(self, request, *args, **kwargs):
        """Удалить похожие слова."""
        word = self.get_object()
        try:
            similar = Similar.objects.get(pk=kwargs.get('similar_id'))
        except Similar.DoesNotExist:
            raise NotFound(detail='The similar not found')

        match request.method:
            case 'DELETE':
                similar.delete()
                similars = Similar.objects.filter(to_word=word)
                serializer = SimilarSerializer(
                    similars, many=True, context={'request': request}
                )
                return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(list=extend_schema(operation_id='types_list'))
class TypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Просмотр списка всех возможных типов слов и фраз."""

    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    lookup_field = 'slug'
    http_method_names = ('get',)
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


@extend_schema_view(
    list=extend_schema(operation_id='formsgroups_list'),
    create=extend_schema(operation_id='formsgroup_create'),
    retrieve=extend_schema(operation_id='formsgroup_retrieve'),
    partial_update=extend_schema(operation_id='formsgroup_partial_update'),
    destroy=extend_schema(operation_id='formsgroup_destroy'),
)
class FormsGroupsViewSet(viewsets.ModelViewSet):
    """
    Просмотр списка всех групп форм пользователя и добавление новых групп.
    """

    serializer_class = FormsGroupSerializer
    lookup_field = 'slug'
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthenticated,)
    queryset = FormsGroup.objects.none()
    pagination_class = None
    filter_backends = (filters.SearchFilter,)  # добавить фильтр по языку
    search_fields = ('name',)

    def get_queryset(self):
        user = self.request.user
        admin_user = User.objects.get(username='admin')
        # добавить проверку наличия пользователя админа
        return FormsGroup.objects.filter(
            Q(author=user) | Q(author=admin_user)
        ).annotate(words_count=Count('words', distinct=True))


@extend_schema_view(
    list=extend_schema(operation_id='collections_list'),
    create=extend_schema(operation_id='collection_create'),
    retrieve=extend_schema(operation_id='collection_retrieve'),
    partial_update=extend_schema(operation_id='collection_partial_update'),
    destroy=extend_schema(operation_id='collection_destroy'),
)
class CollectionViewSet(viewsets.ModelViewSet):
    """Действия с коллекциями."""

    lookup_field = 'slug'
    http_method_names = ('get', 'post', 'head', 'patch', 'delete')
    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)
    queryset = Collection.objects.none()
    pagination_class = LimitPagination
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    )
    filterset_class = CollectionFilter
    ordering = ('-created',)
    ordering_fields = ('created', 'title')
    search_fields = ('title',)

    def get_serializer_class(self):
        match self.action:
            case 'list' | 'favorites':
                return CollectionShortSerializer
            case 'add_to_favorites':
                return CollectionsListSerializer
            case _:
                return CollectionSerializer

    def get_queryset(self):
        user = self.request.user
        match self.action:
            case 'favorites':
                return Collection.objects.filter(favorite_for__user=user).order_by(
                    '-favorite_for__created'
                )
            case _:
                return user.collections.annotate(
                    words_count=Count('words', distinct=True)
                )

    @extend_schema(operation_id='collection_favorite_create')
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, slug):
        """Добавить коллекцию в избранное."""
        collection = self.get_object()
        _, created = FavoriteCollection.objects.get_or_create(
            user=request.user, collection=collection
        )
        if not created:
            return Response(
                {'detail': 'Эта коллекция уже в избранном.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response({'favorite': True}, status=status.HTTP_201_CREATED)

    @extend_schema(operation_id='collection_favorite_destroy')
    @favorite.mapping.delete
    def remove_from_favorite(self, request, slug):
        """Удалить коллекцию из избранного."""
        collection = self.get_object()
        deleted, _ = FavoriteCollection.objects.filter(
            collection=collection, user=request.user
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Коллекции нет в избранном.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({'favorite': False}, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(operation_id='collections_favorite_list')
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def favorites(self, request):
        """Получить список избранных коллекций."""
        return self.list(request)

    @extend_schema(operation_id='collections_favorite_list_create')
    @favorites.mapping.post
    def add_to_favorites(self, request):
        """Добавить список коллекций в избранное."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        collections = serializer.validated_data.get('collections')
        created_favorites = []

        with transaction.atomic():
            for collection in collections:
                obj, created = FavoriteCollection.objects.get_or_create(
                    user=request.user, collection=collection
                )
                if created:
                    created_favorites.append(collection.title)

        if not created_favorites:
            return Response(
                {'detail': 'Все коллекции уже в избранном.'},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                'created': len(created_favorites),
                'added_to_favorites': created_favorites,
            },
            status=status.HTTP_201_CREATED,
        )
