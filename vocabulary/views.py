"""Обработчики приложения vocabulary."""

import random

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiParameter, OpenApiTypes, extend_schema, extend_schema_view,
)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.pagination import LimitPagination

from .filters import WordFilter
from .models import (
    Definition, FormsGroup, WordTranslation, Type, UsageExample,
    WordDefinitions,
    WordTranslations, WordUsageExamples, Collection, FavoriteCollection,
)
from .permissions import (
    CanAddDefinitionPermission, CanAddUsageExamplePermission,
    IsAuthorOrReadOnly,
)
from .serializers import (
    CollectionSerializer, CollectionShortSerializer, DefinitionSerializer,
    FormsGroupSerializer, TranslationSerializer, TypeSerializer,
    UsageExampleSerializer, WordSerializer, WordShortSerializer,
)

User = get_user_model()


@extend_schema(tags=['vocabulary'])
@extend_schema_view(
    list=extend_schema(
        summary='Просмотр списка слов из своего словаря',
        responses={
            status.HTTP_200_OK: WordShortSerializer,
        },
        description=(
                'Просмотреть список своих слов с пагинацией и применением '
                'фильтров, сортировки и поиска. Нужна авторизация.'
        ),
        parameters=[
            OpenApiParameter(
                "created", OpenApiTypes.DATETIME, OpenApiParameter.QUERY,
                description=(
                        'Фильтр по дате добавления. Включая сравнение больше и '
                        'меньше: created__gt и created__lt.'
                )
            ),
            OpenApiParameter(
                "created__year", OpenApiTypes.INT, OpenApiParameter.QUERY,
                description=(
                        'Фильтр по году добавления. Включая сравнение больше и '
                        'меньше: created__year__gt и created__year__lt.'
                )
            ),
            OpenApiParameter(
                "created__month", OpenApiTypes.INT, OpenApiParameter.QUERY,
                description=(
                        'Фильтр по месяцу добавления. Включая сравнение больше и '
                        'меньше: created__month__gt и created__month__lt.'
                )
            ),
            OpenApiParameter(
                "language", OpenApiTypes.STR, OpenApiParameter.QUERY,
                description=(
                        'Фильтр по языку. Принимает isocode языка.'
                )
            ),
            OpenApiParameter(
                "is_problematic", OpenApiTypes.BOOL, OpenApiParameter.QUERY,
                description=(
                        'Фильтр по метке "проблемное".'
                )
            ),
            OpenApiParameter(
                "tags", OpenApiTypes.STR, OpenApiParameter.QUERY,
                description=(
                        'Фильтр по тегам. Принимает name тегов через запятую, '
                        'если несколько.'
                )
            ),
            OpenApiParameter(
                "activity", OpenApiTypes.STR, OpenApiParameter.QUERY,
                description=(
                        'Фильтр по статусу активности. Принимает варианты '
                        'INACTIVE, ACTIVE, MASTERED.'
                )
            ),
            OpenApiParameter(
                "types", OpenApiTypes.STR, OpenApiParameter.QUERY,
                description=(
                        'Фильтр по типам. Принимает slug типов через запятую, '
                        'если несколько.'
                )
            ),
            OpenApiParameter(
                "first_letter", OpenApiTypes.STR, OpenApiParameter.QUERY,
                description=(
                        'Фильтр по первой букве слова.'
                )
            ),
            OpenApiParameter(
                "translations_count", OpenApiTypes.INT, OpenApiParameter.QUERY,
                description=(
                        'Фильтр по кол-ву переводов. Включая сравнение больше и '
                        'меньше: translations_count__gt и translations_count__lt.'
                )
            ),
            OpenApiParameter(
                "examples_count", OpenApiTypes.INT, OpenApiParameter.QUERY,
                description=(
                        'Фильтр по кол-ву примеров. Включая сравнение больше и '
                        'меньше: examples_count__gt и examples_count__lt.'
                )
            ),
        ],
    ),
    create=extend_schema(
        summary='Добавление нового слова в свой словарь',
        request=WordSerializer,
        responses={
            status.HTTP_201_CREATED: WordSerializer,
        },
    ),
    retrieve=extend_schema(
        summary='Просмотр профиля слова',
        responses={
            status.HTTP_200_OK: WordSerializer,
        },
    ),
    partial_update=extend_schema(
        summary='Редактирование слова из своего словаря',
        responses={
            status.HTTP_200_OK: WordSerializer,
        },
    ),
    destroy=extend_schema(
        summary='Удаление слова из своего словаря',
        responses={
            status.HTTP_204_NO_CONTENT: None,
        },
    )
)
class WordViewSet(viewsets.ModelViewSet):
    """Действия со словами из своего словаря."""

    lookup_field = 'slug'
    http_method_names = ('get', 'post', 'head', 'patch', 'delete')
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    )
    filterset_class = WordFilter
    ordering = ('-created',)
    ordering_fields = ('created', 'text', 'translations_count')
    search_fields = (
        'text', 'translations__text',
        'tags__name', 'definitions__text',
        'definitions__translation'
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
                collections_count=Count('collections', distinct=True)
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
            case _:
                return WordSerializer

    @extend_schema(summary='Получить случайное слово из своего словаря')
    @action(methods=['get'], detail=False)
    def random(self, request, *args, **kwargs):
        """Получить случайное слово из словаря."""
        queryset = self.filter_queryset(self.get_queryset())
        word = random.choice(queryset) if queryset else None
        serializer = self.get_serializer(
            word, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary='Просмотр списка всех переводов слова',
        responses={
            status.HTTP_200_OK: TranslationSerializer,
        },
        methods=['get']
    )
    @extend_schema(
        summary='Добавление нового перевода к слову',
        request=TranslationSerializer,
        responses={
            status.HTTP_201_CREATED: TranslationSerializer,
        },
        methods=['post']
    )
    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=TranslationSerializer,
        permission_classes=[IsAuthenticated]
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

                new_translation = serializer.save(
                    author_id=request.user.id
                )

                WordTranslations.objects.create(
                    translation=new_translation,
                    word=word
                )
                return Response(
                    self.get_serializer(new_translation).data,
                    status=status.HTTP_201_CREATED
                )

    @extend_schema(
        summary='Просмотр перевода слова',
        responses={
            status.HTTP_200_OK: TranslationSerializer,
        },
        methods=['get']
    )
    @extend_schema(
        summary='Редактирование перевода слова',
        request=TranslationSerializer,
        responses={
            status.HTTP_200_OK: TranslationSerializer,
        },
        methods=['patch']
    )
    @extend_schema(
        summary='Удаление перевода слова',
        responses={
            status.HTTP_204_NO_CONTENT: None,
        },
        methods=['delete']
    )
    @action(
        detail=True,
        methods=['patch', 'delete'],
        url_path=r'translations/(?P<translation_id>\d+)',
        url_name="word's translations detail",
        serializer_class=TranslationSerializer
    )
    def translations_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить перевод слова."""
        word = self.get_object()
        try:
            translation = word.translations.get(
                pk=kwargs.get('translation_id')
            )
        except WordTranslation.DoesNotExist:
            raise NotFound(detail="The translation not found")

        match request.method:
            case 'PATCH':
                serializer = self.get_serializer(
                    instance=translation,
                    data=request.data,
                    partial=True
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
                return Response(
                    serializer.data,
                    status=status.HTTP_204_NO_CONTENT
                )

    @extend_schema(
        summary='Просмотр списка всех определений слова',
        responses={
            status.HTTP_200_OK: DefinitionSerializer,
        },
        methods=['get']
    )
    @extend_schema(
        summary='Добавление нового определения к слову',
        request=DefinitionSerializer,
        responses={
            status.HTTP_201_CREATED: DefinitionSerializer,
        },
        methods=['post']
    )
    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=DefinitionSerializer,
        permission_classes=[IsAuthenticated, CanAddDefinitionPermission]
    )
    def definitions(self, request, *args, **kwargs):
        """Получить все определения слова или добавить новое определение."""
        word = self.get_object()
        defs = word.definitions.all()

        match request.method:
            case 'GET':
                return Response(
                    self.get_serializer(defs, many=True).data,
                    status=status.HTTP_200_OK
                )
            case 'POST':
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                new_def = serializer.save(
                    **serializer.validated_data
                )
                WordDefinitions.objects.create(definition=new_def, word=word)
                return Response(
                    self.get_serializer(new_def).data,
                    status=status.HTTP_201_CREATED
                )

    @extend_schema(
        summary='Просмотр определения слова',
        responses={
            status.HTTP_200_OK: DefinitionSerializer,
        },
        methods=['get']
    )
    @extend_schema(
        summary='Редактирование определения слова',
        request=DefinitionSerializer,
        responses={
            status.HTTP_200_OK: DefinitionSerializer,
        },
        methods=['patch']
    )
    @extend_schema(
        summary='Удаление определения слова',
        responses={
            status.HTTP_204_NO_CONTENT: None,
        },
        methods=['delete']
    )
    @action(
        detail=True,
        methods=['get', 'patch', 'delete'],
        url_path=r'definitions/(?P<definition_id>\d+)',
        url_name="word's definition detail",
        serializer_class=DefinitionSerializer
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

    @extend_schema(
        summary='Просмотр списка всех примеров использования слова',
        responses={
            status.HTTP_200_OK: UsageExampleSerializer,
        },
        methods=['get']
    )
    @extend_schema(
        summary='Добавление нового примера использования к слову',
        request=UsageExampleSerializer,
        responses={
            status.HTTP_201_CREATED: UsageExampleSerializer,
        },
        methods=['post']
    )
    @action(
        methods=['get', 'post'],
        detail=True,
        serializer_class=UsageExampleSerializer,
        permission_classes=[IsAuthenticated, CanAddUsageExamplePermission]
    )
    def examples(self, request, *args, **kwargs):
        """Получить все примеры слова или добавить новый пример."""
        word = self.get_object()
        _examples = word.examples.all()
        match request.method:
            case 'GET':
                return Response(
                    self.get_serializer(_examples, many=True).data,
                    status=status.HTTP_200_OK
                )
            case 'POST':
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                new_example = serializer.save(
                    **serializer.validated_data
                )
                WordUsageExamples.objects.create(
                    example=new_example,
                    word=word
                )
                return Response(
                    self.get_serializer(new_example).data,
                    status=status.HTTP_201_CREATED
                )

    @extend_schema(
        summary='Просмотр примера использования слова',
        responses={
            status.HTTP_200_OK: UsageExampleSerializer,
        },
        methods=['get']
    )
    @extend_schema(
        summary='Редактирование примера использования слова',
        request=UsageExampleSerializer,
        responses={
            status.HTTP_200_OK: UsageExampleSerializer,
        },
        methods=['patch']
    )
    @extend_schema(
        summary='Удаление примера использования слова',
        responses={
            status.HTTP_204_NO_CONTENT: None,
        },
        methods=['delete']
    )
    @action(
        detail=True,
        methods=['get', 'patch', 'delete'],
        url_path=r'examples/(?P<example_id>\d+)',
        url_name="word's usage example detail",
        serializer_class=UsageExampleSerializer
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

    @extend_schema(
        summary='Изменить метку "проблемное" у слова',
        request=None,
        responses={
            status.HTTP_200_OK: WordSerializer,
        }
    )
    @action(
        detail=True,
        methods=['post'],
        url_path='problematic-toggle',
        serializer_class=WordShortSerializer
    )
    def problematic(self, request, *args, **kwargs):
        """Изменить значение метки is_problematic слова."""
        word = self.get_object()
        word.is_problematic = not word.is_problematic
        word.save()
        return Response(self.get_serializer(word).data)


@extend_schema(tags=['types'])
@extend_schema_view(
    list=extend_schema(
        summary=(
                'Просмотр списка всех возможных типов и частей речи слов и фраз'
        ),
        responses={
            status.HTTP_200_OK: TypeSerializer,
        },
    )
)
class TypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Просмотр списка всех возможных типов слов и фраз."""

    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    lookup_field = 'slug'
    http_method_names = ('get',)
    pagination_class = None
    permission_classes = (
        AllowAny,
    )
    filter_backends = (
        filters.SearchFilter,
    )
    search_fields = (
        'name',
    )


@extend_schema(tags=['forms-groups'])
@extend_schema_view(
    list=extend_schema(
        summary=(
                'Просмотр списка всех групп форм пользователя'
        ),
        responses={
            status.HTTP_200_OK: FormsGroupSerializer,
        },
    )
)
class FormsGroupsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Просмотр списка всех групп форм пользователя."""

    queryset = FormsGroup.objects.all()
    serializer_class = FormsGroupSerializer
    lookup_field = 'slug'
    http_method_names = ('get',)
    pagination_class = None
    permission_classes = (
        IsAuthenticated,
    )
    filter_backends = (
        filters.SearchFilter,
    )  # добавить фильтр по языку
    search_fields = (
        'name',
    )

    def get_queryset(self):
        user = self.request.user
        return user.formsgroups.annotate(
            words_count=Count('words', distinct=True)
        )


@extend_schema(tags=['collections'])
@extend_schema_view(
    list=extend_schema(
        summary=(
                'Просмотр списка всех коллекций пользователя'
        ),
        responses={
            status.HTTP_200_OK: CollectionSerializer,
        },
    ),
    create=extend_schema(
        summary='Добавление новой коллекции',
        responses={
            status.HTTP_201_CREATED: CollectionSerializer,
        },
    ),
    retrieve=extend_schema(
        summary='Просмотр коллекции',
        responses={
            status.HTTP_200_OK: CollectionSerializer,
        },
    ),
    partial_update=extend_schema(
        summary='Редактирование коллекции',
        responses={
            status.HTTP_200_OK: CollectionSerializer,
        },
    ),
    destroy=extend_schema(
        summary='Удаление коллекции',
        responses={
            status.HTTP_204_NO_CONTENT: None,
        },
    )
)
class CollectionViewSet(viewsets.ModelViewSet):
    """Действия с коллекциями."""

    lookup_field = 'slug'
    http_method_names = ('get', 'post', 'head', 'patch', 'delete')
    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)
    pagination_class = LimitPagination
    filter_backends = (
        filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend
    )
    ordering = ('-created',)

    def get_serializer_class(self):
        match self.action:
            case 'list':
                return CollectionShortSerializer
            case _:
                return CollectionSerializer

    def get_queryset(self):
        user = self.request.user
        return user.collections.annotate(
            words_count=Count('words', distinct=True)
        )

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, slug):
        """Добавить коллекцию в избранное."""
        collection = get_object_or_404(Collection, slug=slug)
        _, created = FavoriteCollection.objects.get_or_create(
            user=request.user,
            collection=collection)
        if not created:
            return Response({'detail': 'Эта коллекция уже в избранном.'},
                            status=status.HTTP_409_CONFLICT)
        return Response({'favorite': True}, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def remove_from_favorite(self, request, slug):
        """Удалить коллекцию из избранного."""
        collection = get_object_or_404(Collection, slug=slug)
        deleted, _ = FavoriteCollection.objects.filter(
            collection=collection, user=request.user).delete()
        if deleted:
            return Response({"favorite": False},
                            status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'detail': 'Коллекции нет в избранном.'},
                            status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'],
            permission_classes=[IsAuthenticated])
    def favorites(self, request):
        """Получить список избранных коллекций."""
        favorites = Collection.objects.filter(
            favorite_for__user=request.user).order_by('-favorite_for__created')
        serializer = CollectionShortSerializer(favorites, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @favorites.mapping.post
    def add_to_favorites(self, request):
        """Добавить список коллекций в избранное."""
        slugs = request.data.get('slugs')
        if not slugs:
            return Response({'detail': 'Пустой список слагов.'},
                            status=status.HTTP_400_BAD_REQUEST)

        collections = Collection.objects.filter(slug__in=slugs)
        created_favorites = []
        with transaction.atomic():
            for collection in collections:
                obj, created = FavoriteCollection.objects.get_or_create(
                    user=request.user, collection=collection)
                if created:
                    created_favorites.append(
                        collection.title)

        if not created_favorites:
            return Response(
                {'detail': 'Все коллекции уже в избранном.'},
                status=status.HTTP_400_BAD_REQUEST)

        return Response({'created': len(created_favorites),
                         'added_to_favorites': created_favorites},
                        status=status.HTTP_201_CREATED)
