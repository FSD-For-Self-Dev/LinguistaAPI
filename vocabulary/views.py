"""Обработчики приложения vocabulary."""

import random

from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.db.models import Count, Q

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

from .filters import CollectionFilter, WordFilter
from .models import (
    Collection,
    FavoriteCollection,
    FormsGroup,
    Type,
    WordDefinitions,
    WordTranslation,
    WordTranslations,
    WordUsageExamples,
    Word,
    Synonym,
    Antonym,
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
    SynonymSerializer,
    AntonymSerializer,
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
    http_method_names = ('get', 'post', 'patch', 'delete')
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
            case 'antonyms' | 'antonyms_detail':
                return AntonymSerializer
            case _:
                return WordSerializer

    def create(self, request, *args, **kwargs):
        """Обработать ошибку IntegrityError перед созданием слова."""
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            word = request.data.get('text')
            return Response(
                {'detail': f'Слово или фраза {word} уже есть в вашем словаре.'},
                status=status.HTTP_409_CONFLICT,
            )

    @extend_schema(operation_id='word_random')
    @action(methods=['get'], detail=False, serializer_class=WordShortSerializer)
    def random(self, request, *args, **kwargs):
        """Получить случайное слово из словаря."""
        queryset = self.filter_queryset(self.get_queryset())
        word = random.choice(queryset) if queryset else None
        return Response(
            self.get_serializer(word, many=False, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(operation_id='problematic_toggle')
    @action(
        methods=['post'],
        detail=True,
        url_path='problematic-toggle',
        serializer_class=WordSerializer,
    )
    def problematic(self, request, *args, **kwargs):
        """Изменить значение метки is_problematic слова."""
        word = self.get_object()
        word.is_problematic = not word.is_problematic
        word.save()
        return Response(self.get_serializer(word).data, status=status.HTTP_201_CREATED)

    def _list_and_create_action(
        self,
        request,
        objs_name,
        relation_model=None,
        relation_field=None,
        *args,
        **kwargs,
    ):
        """Осуществить методы list, create для дополнений слова."""
        word = self.get_object()
        _objs = word.__getattribute__(objs_name).all()
        match request.method:
            case 'GET':
                serializer = self.get_serializer(
                    _objs, many=True, context={'request': request}
                )
                return Response(serializer.data, status=status.HTTP_200_OK)
            case 'POST':
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                try:
                    _new_obj = serializer.save(author_id=request.user.id)
                except IntegrityError:
                    return Response(
                        {'detail': kwargs.get('integrityerror_msg', '')},
                        status=status.HTTP_409_CONFLICT,
                    )

                if relation_model:
                    relation_model.objects.create(
                        **{relation_field: _new_obj}, word=word
                    )

                return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _detail_action(
        self, request, objs_name, lookup_name, relation_model=None, *args, **kwargs
    ):
        """Осуществить методы retrieve, partial_update, destroy для дополнений слова."""
        word = self.get_object()
        try:
            _obj = word.__getattribute__(objs_name).get(pk=kwargs.get(lookup_name))
        except relation_model.DoesNotExist:
            raise NotFound(detail=kwargs.get('notfounderror_msg', ''))

        match request.method:
            case 'GET':
                return Response(self.get_serializer(_obj).data)
            case 'PATCH':
                serializer = self.get_serializer(
                    instance=_obj, data=request.data, partial=True
                )
                serializer.is_valid(raise_exception=True)
                try:
                    serializer.save()
                except IntegrityError:
                    return Response(
                        {'detail': kwargs.get('integrityerror_msg', '')},
                        status=status.HTTP_409_CONFLICT,
                    )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            case 'DELETE':
                _obj.delete()
                objs = word.__getattribute__(objs_name).all()
                serializer = self.get_serializer(
                    objs, many=True, context={'request': request}
                )
                return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(operation_id='translations_list', methods=['get'])
    @extend_schema(operation_id='translation_create', methods=['post'])
    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=TranslationSerializer,
    )
    def translations(self, request, *args, **kwargs):
        """Получить все переводы слова или добавить новый перевод."""
        return self._list_and_create_action(
            request,
            'translations',
            integrityerror_msg='Такой перевод уже существует.',
            relation_model=WordTranslations,
            relation_field='translation',
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='translations_retrieve', methods=['get'])
    @extend_schema(operation_id='translation_partial_update', methods=['patch'])
    @extend_schema(operation_id='translation_destroy', methods=['delete'])
    @action(
        methods=['get', 'patch', 'delete'],
        detail=True,
        url_path=r'translations/(?P<translation_id>\d+)',
        serializer_class=TranslationSerializer,
    )
    def translations_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить перевод слова."""
        return self._detail_action(
            request,
            'translations',
            notfounderror_msg='Перевод с таким id у слова не найден.',
            relation_model=WordTranslation,
            lookup_name='translation_id',
            integrityerror_msg='Такой перевод уже существует.',
            *args,
            **kwargs,
        )

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
        return self._list_and_create_action(
            request,
            'definitions',
            integrityerror_msg='Такое определение уже существует.',
            relation_model=WordDefinitions,
            relation_field='definition',
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
        return self._detail_action(
            request,
            'definitions',
            notfounderror_msg='Определение с таким id у слова не найдено.',
            relation_model=WordDefinitions,
            lookup_name='definition_id',
            integrityerror_msg='Такое определение уже существует.',
            *args,
            **kwargs,
        )

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
        return self._list_and_create_action(
            request,
            'examples',
            integrityerror_msg='Такой пример уже существует.',
            relation_model=WordUsageExamples,
            relation_field='example',
        )

    @extend_schema(operation_id='example_retrieve', methods=['get'])
    @extend_schema(operation_id='example_partial_update', methods=['patch'])
    @extend_schema(operation_id='example_destroy', methods=['delete'])
    @action(
        methods=['get', 'patch', 'delete'],
        detail=True,
        url_path=r'examples/(?P<example_id>\d+)',
        serializer_class=UsageExampleSerializer,
    )
    def examples_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить пример использования слова."""
        return self._detail_action(
            request,
            'examples',
            notfounderror_msg='Пример с таким id у слова не найден.',
            relation_model=WordUsageExamples,
            lookup_name='example_id',
            integrityerror_msg='Такой пример уже существует.',
            *args,
            **kwargs,
        )

    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=SynonymSerializer,
    )
    def synonyms(self, request, *args, **kwargs):
        """Получить все синонимы слова или добавить новый синоним."""
        return self._list_and_create_action(
            request,
            'synonym_to_words',
            integrityerror_msg='Такой синоним уже существует.',
        )

    @action(
        methods=['get', 'patch', 'delete'],
        detail=True,
        url_path=r'synonyms/(?P<synonym_id>\d+)',
        serializer_class=SynonymSerializer,
    )
    def synonyms_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить синоним слова."""
        return self._detail_action(
            request,
            'synonym_to_words',
            notfounderror_msg='Синоним с таким id у слова не найден.',
            relation_model=Synonym,
            lookup_name='synonym_id',
            integrityerror_msg='Такой синоним уже существует.',
            *args,
            **kwargs,
        )

    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=AntonymSerializer,
    )
    def antonyms(self, request, *args, **kwargs):
        """Получить все антонимы слова или добавить новый антоним."""
        return self._list_and_create_action(
            request,
            'antonym_to_words',
            integrityerror_msg='Такой антоним уже существует.',
        )

    @action(
        methods=['get', 'delete'],
        detail=True,
        url_path=r'antonyms/(?P<antonym_id>\d+)',
        serializer_class=AntonymSerializer,
    )
    def antonyms_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить антоним слова."""
        return self._detail_action(
            request,
            'antonym_to_words',
            notfounderror_msg='Антоним с таким id у слова не найден.',
            relation_model=Antonym,
            lookup_name='antonym_id',
            integrityerror_msg='Такой антоним уже существует.',
            *args,
            **kwargs,
        )


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
    http_method_names = ('get', 'post', 'patch', 'delete')
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
