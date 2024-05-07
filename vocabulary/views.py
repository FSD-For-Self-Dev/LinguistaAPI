"""Обработчики приложения vocabulary."""

import random
from itertools import chain

from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.db.models import Count, Q, F
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.exceptions import NotFound

from core.pagination import LimitPagination
from core.exceptions import AmountLimitExceeded, ObjectAlreadyExist
from core.mixins import (
    ActionsWithRelatedObjectsMixin,
    ObjectAlreadyExistHandler,
    DestroyReturnListMixin,
    FavoriteMixin,
)
from languages.serializers import LanguageSerailizer
from users.models import (
    UserDefaultWordsView,
    UserLearningLanguage,
)
from users.serializers import (
    LearningLanguageSerailizer,
    NativeLanguageSerailizer,
)
from users.constants import UsersAmountLimits

from .constants import VocabularyAmountLimits
from .filters import CollectionFilter, WordFilter
from .models import (
    Collection,
    FormsGroup,
    Type,
    Definition,
    WordTranslation,
    UsageExample,
    Word,
    Tag,
    Synonym,
    Antonym,
    Form,
    Similar,
    ImageAssociation,
    QuoteAssociation,
    Note,
    FavoriteCollection,
    FavoriteWord,
    Language,
)
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    WordShortCardSerializer,
    WordLongCardSerializer,
    WordStandartCardSerializer,
    WordShortCreateSerializer,
    WordSerializer,
    WordTranslationInLineSerializer,
    WordTranslationForWordSerializer,
    WordTranslationSerializer,
    WordTranslationCreateSerializer,
    WordTranslationListSerializer,
    UsageExampleInLineSerializer,
    UsageExampleForWordSerializer,
    UsageExampleSerializer,
    UsageExampleCreateSerializer,
    UsageExampleListSerializer,
    DefinitionInLineSerializer,
    DefinitionForWordSerializer,
    DefinitionSerializer,
    DefinitionCreateSerializer,
    DefinitionListSerializer,
    SynonymForWordListSerializer,
    SynonymForWordSerializer,
    SynonymSerializer,
    AntonymForWordListSerializer,
    AntonymForWordSerializer,
    AntonymSerializer,
    FormForWordListSerializer,
    FormForWordSerializer,
    SimilarForWordListSerializer,
    SimilarForWordSerailizer,
    SimilarSerializer,
    MultipleWordsSerializer,
    TagListSerializer,
    TypeSerializer,
    FormsGroupListSerializer,
    CollectionShortSerializer,
    CollectionSerializer,
    NoteInLineSerializer,
    NoteForWordSerializer,
    ImageInLineSerializer,
    ImageListSerializer,
    ImageForWordSerializer,
    ImageShortSerailizer,
    QuoteInLineSerializer,
    QuoteForWordSerializer,
    AssociationsCreateSerializer,
    LearningLanguageWithLastWordsSerailizer,
    LearningLanguageShortSerailizer,
    MainPageSerailizer,
)

User = get_user_model()


def get_words_view(request):
    words_view = {
        'standart': WordStandartCardSerializer,
        'short': WordShortCardSerializer,
        'long': WordLongCardSerializer,
    }
    default_words_view = 'standart'

    words_view_param = request.query_params.get('view', None)
    if not words_view_param:
        try:
            words_view_param = UserDefaultWordsView.objects.get(
                user=request.user
            ).words_view
        except Exception:
            words_view_param = default_words_view
    return words_view.get(words_view_param)


class ActionsWithRelatedWordsMixin(ActionsWithRelatedObjectsMixin):
    def retrieve_with_words(
        self,
        request,
        default_order='-created',
        words_related_name='words',
        words=None,
        *args,
        **kwargs,
    ):
        queryset = self.get_queryset()
        instance = get_object_or_404(
            queryset, **{self.lookup_field: self.kwargs[self.lookup_field]}
        )
        response_data = self.get_serializer(instance).data
        _words = (
            words
            if words is not None
            else instance.__getattribute__(words_related_name)
        )
        _words = _words.annotate(
            translations_count=Count('translations', distinct=True),
            examples_count=Count('examples', distinct=True),
            collections_count=Count('collections', distinct=True),
        ).order_by(default_order)
        words_serializer = get_words_view(request)
        words_data = self.get_filtered_paginated_objs(
            request, _words, WordViewSet, words_serializer
        )
        return Response(
            {
                **response_data,
                'words': words_data,
            }
        )

    def create_return_with_words(
        self,
        request,
        default_order='-created',
        words_related_name='words',
        *args,
        **kwargs,
    ):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        _words = (
            instance.__getattribute__(words_related_name)
            .annotate(
                translations_count=Count('translations', distinct=True),
                examples_count=Count('examples', distinct=True),
                collections_count=Count('collections', distinct=True),
            )
            .order_by(default_order)
        )
        words_serializer = get_words_view(request)
        words_data = self.paginate_related_objs(request, _words, words_serializer)
        return Response(
            {
                **serializer.data,
                'words': words_data,
            },
            status=status.HTTP_201_CREATED,
        )

    def partial_update_return_with_words(
        self,
        request,
        default_order='-created',
        words_related_name='words',
        *args,
        **kwargs,
    ):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        _words = (
            instance.__getattribute__(words_related_name)
            .annotate(
                translations_count=Count('translations', distinct=True),
                examples_count=Count('examples', distinct=True),
                collections_count=Count('collections', distinct=True),
            )
            .order_by(default_order)
        )
        words_serializer = get_words_view(request)
        words_data = self.paginate_related_objs(request, _words, words_serializer)
        return Response(
            {
                **serializer.data,
                'words': words_data,
            }
        )

    def add_words_return_with_words(
        self,
        request,
        default_order='-created',
        words_related_name='words',
        *args,
        **kwargs,
    ):
        instance = self.get_object()
        response_data = self.create_related_objs(
            request,
            objs_related_name=words_related_name,
            serializer=WordShortCreateSerializer,
            related_model=Word,
            set_objs=True,
            instance=instance,
        ).data
        _words = (
            instance.__getattribute__(words_related_name)
            .annotate(
                translations_count=Count('translations', distinct=True),
                examples_count=Count('examples', distinct=True),
                collections_count=Count('collections', distinct=True),
            )
            .order_by(default_order)
        )
        words_serializer = get_words_view(request)
        words_data = self.paginate_related_objs(request, _words, words_serializer)
        return Response(
            {
                **response_data,
                'words': words_data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=['vocabulary'])
@extend_schema_view(
    list=extend_schema(operation_id='words_list'),
    create=extend_schema(operation_id='word_create'),
    retrieve=extend_schema(operation_id='word_retrieve'),
    partial_update=extend_schema(operation_id='word_partial_update'),
    destroy=extend_schema(operation_id='word_destroy'),
)
class WordViewSet(
    ActionsWithRelatedObjectsMixin,
    ObjectAlreadyExistHandler,
    DestroyReturnListMixin,
    FavoriteMixin,
    viewsets.ModelViewSet,
):
    """Действия со словами из своего словаря."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'slug'
    queryset = Word.objects.none()
    serializer_class = WordSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    )
    filterset_class = WordFilter
    ordering = ('-created',)
    ordering_fields = (
        'text',
        'translations_count',
        'last_exercise_date',
        'created',
    )
    search_fields = (
        'text',
        'translations__text',
        'tags__name',
        'definitions__text',
        'definitions__translation',
        'examples__text',
        'examples__translation',
    )

    def get_queryset(self):
        user = self.request.user
        match self.action:
            case 'favorites':
                return Word.objects.filter(favorite_for__user=user).order_by(
                    '-favorite_for__created'
                )
            case _:
                return user.words.annotate(
                    translations_count=Count('translations', distinct=True),
                    examples_count=Count('examples', distinct=True),
                    collections_count=Count('collections', distinct=True),
                )

    def get_serializer_class(self):
        match self.action:
            case 'list' | 'destroy' | 'multiple_create' | 'favorites':
                return get_words_view(self.request)
            case 'notes_detail' | 'notes_create':
                return NoteForWordSerializer
            case 'delete_note':
                return WordSerializer
            case _:
                return super().get_serializer_class()

    @extend_schema(operation_id='word_random')
    @action(
        methods=('get',),
        detail=False,
        serializer_class=WordStandartCardSerializer,
    )
    def random(self, request, *args, **kwargs):
        """Получить случайное слово из словаря."""
        queryset = self.filter_queryset(self.get_queryset())
        word = random.choice(queryset) if queryset else None
        return Response(
            self.get_serializer(word, many=False, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(operation_id='word_problematic_toggle')
    @action(
        methods=('post',),
        detail=True,
        url_path='problematic-toggle',
        serializer_class=WordSerializer,
    )
    def problematic(self, request, *args, **kwargs):
        """Изменить значение метки is_problematic слова."""
        word = self.get_object()
        word.is_problematic = not word.is_problematic
        word.save()
        return Response(
            self.get_serializer(word).data,
            status=status.HTTP_201_CREATED,
        )

    @transaction.atomic
    @extend_schema(operation_id='word_multiple_create')
    @action(
        methods=('post',),
        detail=False,
        url_path='multiple-create',
    )
    def multiple_create(self, request, *args, **kwargs):
        """Быстрое добавление нескольких слов сразу в словарь пользователя."""
        serializer = MultipleWordsSerializer(
            data=request.data, many=False, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
            words_created_count = len(serializer.validated_data['words'])
            collections_count = len(serializer.validated_data['collections'])
            headers = self.get_success_headers(serializer.data)
            response_data = self.list(request).data
            return Response(
                {
                    **response_data,
                    'words_created_count': words_created_count,
                    'collections_count': collections_count,
                },
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        except ObjectAlreadyExist as exception:
            return exception.get_detail_response(request)

    @extend_schema(operation_id='word_tags_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=TagListSerializer,
    )
    def tags(self, request, *args, **kwargs):
        """Получить все теги слова."""
        return self.list_related_objs(request, objs_related_name='tags')

    @extend_schema(operation_id='word_collections_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=CollectionShortSerializer,
    )
    def collections(self, request, *args, **kwargs):
        """Получить все коллекции с этим словом."""
        return self.list_related_objs(request, objs_related_name='collections')

    @extend_schema(operation_id='word_collections_add', methods=('post',))
    @collections.mapping.post
    def collections_add(self, request, *args, **kwargs):
        """Добавить слово в коллекции."""
        return self.create_related_objs(
            request,
            objs_related_name='collections',
            related_model=Collection,
            set_objs=True,
            response_serializer=WordSerializer,
        )

    @extend_schema(operation_id='word_translations_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=WordTranslationInLineSerializer,
    )
    def translations(self, request, *args, **kwargs):
        """Получить все переводы слова."""
        queryset = self.get_queryset()
        instance = get_object_or_404(
            queryset, **{self.lookup_field: self.kwargs[self.lookup_field]}
        )
        filterby_language_name = request.query_params.get('language', '')
        _objs = (
            instance.translations.filter(language__name=filterby_language_name)
            if filterby_language_name
            else instance.translations.all()
        )
        translations_languages = instance.translations.values_list(
            'language__name', flat=True
        )
        return self.list_related_objs(
            request,
            objs_related_name='translations',
            objs=_objs,
            extra_data={'languages': translations_languages},
        )

    @extend_schema(operation_id='word_translations_create', methods=('post',))
    @translations.mapping.post
    def translations_create(self, request, *args, **kwargs):
        """Добавить новые переводы к слову."""
        return self.create_related_objs(
            request,
            objs_related_name='translations',
            amount_limit=VocabularyAmountLimits.MAX_TRANSLATIONS_AMOUNT,
            related_model=WordTranslation,
            set_objs=True,
            response_serializer=WordSerializer,
        )

    @extend_schema(operation_id='word_translations_retrieve', methods=('get',))
    @extend_schema(operation_id='word_translation_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_translation_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'translations/(?P<translation_slug>[\w-]+)',
        serializer_class=WordTranslationForWordSerializer,
    )
    def translations_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить перевод слова."""
        return self.detail_action(
            request,
            objs_related_name='wordtranslations',
            lookup_field='translation__slug',
            lookup_attr_name='translation_slug',
            list_objs_related_name='translations',
            list_serializer=WordTranslationInLineSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_definitions_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=DefinitionInLineSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def definitions(self, request, *args, **kwargs):
        """Получить все определения слова."""
        return self.list_related_objs(request, objs_related_name='definitions')

    @extend_schema(operation_id='word_definitions_create', methods=('post',))
    @definitions.mapping.post
    def definitions_create(self, request, *args, **kwarg):
        """Добавить новые определения к слову."""
        return self.create_related_objs(
            request,
            objs_related_name='definitions',
            amount_limit=VocabularyAmountLimits.MAX_DEFINITIONS_AMOUNT,
            related_model=Definition,
            set_objs=True,
            response_serializer=WordSerializer,
        )

    @extend_schema(operation_id='word_definition_retrieve', methods=('get',))
    @extend_schema(operation_id='word_definition_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_definition_destroy', methods=('delete',))
    @action(
        detail=True,
        methods=('get', 'patch', 'delete'),
        url_path=r'definitions/(?P<definition_slug>[\w-]+)',
        serializer_class=DefinitionForWordSerializer,
    )
    def definitions_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить определение слова."""
        return self.detail_action(
            request,
            objs_related_name='worddefinitions',
            lookup_field='definition__slug',
            lookup_attr_name='definition_slug',
            list_objs_related_name='definitions',
            list_serializer=DefinitionInLineSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_examples_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=UsageExampleInLineSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def examples(self, request, *args, **kwargs):
        """Получить все примеры слова."""
        return self.list_related_objs(request, objs_related_name='examples')

    @extend_schema(operation_id='word_examples_create', methods=('post',))
    @examples.mapping.post
    def examples_create(self, request, *args, **kwargs):
        """Добавить новые примеры к слову."""
        return self.create_related_objs(
            request,
            objs_related_name='examples',
            amount_limit=VocabularyAmountLimits.MAX_EXAMPLES_AMOUNT,
            related_model=UsageExample,
            set_objs=True,
            response_serializer=WordSerializer,
        )

    @extend_schema(operation_id='word_example_retrieve', methods=('get',))
    @extend_schema(operation_id='word_example_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_example_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'examples/(?P<example_slug>[\w-]+)',
        serializer_class=UsageExampleForWordSerializer,
    )
    def examples_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить пример использования слова."""
        return self.detail_action(
            request,
            objs_related_name='wordusageexamples',
            lookup_field='example__slug',
            lookup_attr_name='example_slug',
            list_objs_related_name='examples',
            list_serializer=UsageExampleInLineSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_notes_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=NoteInLineSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def notes(self, request, *args, **kwargs):
        """Получить все заметки слова."""
        return self.list_related_objs(request, objs_related_name='notes')

    @extend_schema(operation_id='word_notes_create', methods=('post',))
    @notes.mapping.post
    def notes_create(self, request, *args, **kwargs):
        """Добавить новые заметки к слову."""
        return self.create_related_objs(
            request,
            objs_related_name='notes',
            amount_limit=VocabularyAmountLimits.MAX_NOTES_AMOUNT,
            related_model=Note,
            set_objs=False,
            response_serializer=WordSerializer,
        )

    @extend_schema(operation_id='word_note_retrieve', methods=('get',))
    @extend_schema(operation_id='word_note_partial_update', methods=('patch',))
    @action(
        methods=('get', 'patch'),
        detail=True,
        url_path=r'notes/(?P<note_slug>[\w-]+)',
    )
    def notes_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить заметку слова."""
        return self.detail_action(
            request,
            objs_related_name='notes',
            lookup_field='slug',
            lookup_attr_name='note_slug',
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_note_destroy', methods=('delete',))
    @notes_detail.mapping.delete
    def delete_note(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            _obj = instance.notes.get(slug=kwargs.get('note_slug'))
        except ObjectDoesNotExist:
            raise NotFound
        _obj.delete()
        instance_serializer = self.get_serializer(instance)
        return Response(instance_serializer.data, status=status.HTTP_204_NO_CONTENT)

    @extend_schema(operation_id='word_synonyms_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=SynonymForWordListSerializer,
    )
    def synonyms(self, request, *args, **kwargs):
        """Получить все синонимы слова."""
        return self.list_related_objs(
            request, objs_related_name='synonym_to_words', response_objs_name='synonyms'
        )

    @extend_schema(operation_id='word_synonyms_create', methods=('post',))
    @synonyms.mapping.post
    def synonyms_create(self, request, *args, **kwargs):
        """Добавить новые синонимы к слову."""
        return self.create_related_objs(
            request,
            objs_related_name='synonym_to_words',
            response_objs_name='synonyms',
            amount_limit=VocabularyAmountLimits.MAX_SYNONYMS_AMOUNT,
            related_model=Synonym,
            set_objs=False,
            response_serializer=WordSerializer,
        )

    @extend_schema(operation_id='word_synonym_retrieve', methods=('get',))
    @extend_schema(operation_id='word_synonym_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_synonym_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'synonyms/(?P<synonym_slug>[\w-]+)',
        serializer_class=SynonymForWordSerializer,
    )
    def synonyms_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить синоним слова."""
        return self.detail_action(
            request,
            objs_related_name='synonym_to_words',
            lookup_field='from_word__slug',
            lookup_attr_name='synonym_slug',
            response_objs_name='synonyms',
            response_serializer=SynonymForWordListSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_antonyms_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=AntonymForWordListSerializer,
    )
    def antonyms(self, request, *args, **kwargs):
        """Получить все антонимы слова."""
        return self.list_related_objs(
            request, objs_related_name='antonym_to_words', response_objs_name='antonyms'
        )

    @extend_schema(operation_id='word_antonyms_create', methods=('post',))
    @antonyms.mapping.post
    def antonyms_create(self, request, *args, **kwargs):
        """Добавить новые антонимы к слову."""
        return self.create_related_objs(
            request,
            objs_related_name='antonym_to_words',
            response_objs_name='antonyms',
            amount_limit=VocabularyAmountLimits.MAX_ANTONYMS_AMOUNT,
            related_model=Antonym,
            set_objs=False,
            response_serializer=WordSerializer,
        )

    @extend_schema(operation_id='word_antonym_retrieve', methods=('get',))
    @extend_schema(operation_id='word_antonym_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_antonym_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'antonyms/(?P<antonym_slug>[\w-]+)',
        serializer_class=AntonymForWordSerializer,
    )
    def antonyms_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить антоним слова."""
        return self.detail_action(
            request,
            objs_related_name='antonym_to_words',
            lookup_field='from_word__slug',
            lookup_attr_name='antonym_slug',
            response_objs_name='antonyms',
            response_serializer=AntonymForWordListSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_forms_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=FormForWordListSerializer,
    )
    def forms(self, request, *args, **kwargs):
        """Получить все формы слова."""
        return self.list_related_objs(
            request, objs_related_name='form_to_words', response_objs_name='forms'
        )

    @extend_schema(operation_id='word_forms_create', methods=('post',))
    @forms.mapping.post
    def forms_create(self, request, *args, **kwargs):
        """Добавить новые формы к слову."""
        return self.create_related_objs(
            request,
            objs_related_name='form_to_words',
            response_objs_name='forms',
            amount_limit=VocabularyAmountLimits.MAX_FORMS_AMOUNT,
            related_model=Form,
            set_objs=False,
            response_serializer=WordSerializer,
        )

    @extend_schema(operation_id='word_form_retrieve', methods=('get',))
    @extend_schema(operation_id='word_form_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_form_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'forms/(?P<form_slug>[\w-]+)',
        serializer_class=FormForWordSerializer,
    )
    def form_detail(self, request, *args, **kwargs):
        """Получить или удалить форму слова."""
        return self.detail_action(
            request,
            objs_related_name='form_to_words',
            lookup_field='from_word__slug',
            lookup_attr_name='form_slug',
            response_objs_name='forms',
            response_serializer=FormForWordListSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_similars_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=SimilarForWordListSerializer,
    )
    def similars(self, request, *args, **kwargs):
        """Получить все похожие слова."""
        return self.list_related_objs(
            request, objs_related_name='similar_to_words', response_objs_name='similars'
        )

    @extend_schema(operation_id='word_similars_create', methods=('post',))
    @similars.mapping.post
    def similars_create(self, request, *args, **kwargs):
        """Добавить новые похожие слова к слову."""
        return self.create_related_objs(
            request,
            objs_related_name='similar_to_words',
            response_objs_name='similars',
            amount_limit=VocabularyAmountLimits.MAX_SIMILARS_AMOUNT,
            related_model=Similar,
            set_objs=False,
            response_serializer=WordSerializer,
        )

    @extend_schema(operation_id='word_similar_retrieve', methods=('get',))
    @extend_schema(operation_id='word_similar_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_similar_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'similars/(?P<similar_slug>[\w-]+)',
        serializer_class=SimilarForWordSerailizer,
    )
    def similar_detail(self, request, *args, **kwargs):
        """Получить или удалить похожее слово."""
        return self.detail_action(
            request,
            objs_related_name='similar_to_words',
            lookup_field='from_word__slug',
            lookup_attr_name='similar_slug',
            response_objs_name='similars',
            response_serializer=SimilarForWordListSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_associations_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=AssociationsCreateSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def associations(self, request, *args, **kwargs):
        """Получить все ассоциации слова."""
        instance = self.get_object()
        images = ImageInLineSerializer(
            instance.images_associations.all(),
            many=True,
            context={'request': request},
        )
        quotes = QuoteInLineSerializer(
            instance.quotes_associations.all(),
            many=True,
            context={'request': request},
        )
        result_list = sorted(
            chain(quotes.data, images.data),
            key=lambda d: d.get('created'),
            reverse=True,
        )
        return Response(
            {
                'count': len(result_list),
                'associations': result_list,
            }
        )

    @extend_schema(operation_id='word_associations_create', methods=('post',))
    @associations.mapping.post
    @transaction.atomic
    def associations_create(self, request, *args, **kwargs):
        """Добавить новые ассоциации к слову."""
        instance = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            _data = serializer.save()
            _quotes, _images = _data.get('quotes', []), _data.get('images', [])
            if (
                len(_quotes) + instance.quotes_associations.count()
                <= VocabularyAmountLimits.MAX_QUOTES_AMOUNT
            ):
                instance.quotes_associations.add(*_quotes)
            else:
                raise AmountLimitExceeded(
                    detail=VocabularyAmountLimits.get_error_message(
                        VocabularyAmountLimits.MAX_QUOTES_AMOUNT,
                        attr_name='quotes_associations',
                    )
                )
            if (
                len(_images) + instance.images_associations.count()
                <= VocabularyAmountLimits.MAX_IMAGES_AMOUNT
            ):
                instance.images_associations.add(*_images)
            else:
                raise AmountLimitExceeded(
                    detail=VocabularyAmountLimits.get_error_message(
                        VocabularyAmountLimits.MAX_IMAGES_AMOUNT,
                        attr_name='images_associations',
                    )
                )
            return Response(
                WordSerializer(instance, context={'request': request}).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(operation_id='word_image_retrieve', methods=('get',))
    @extend_schema(operation_id='word_image_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_image_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'images/(?P<image_id>[\w\d-]+)',
        serializer_class=ImageForWordSerializer,
    )
    def images_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить ассоциацию-картинку слова."""
        return self.detail_action(
            request,
            objs_related_name='wordimageassociations',
            lookup_field='image__id',
            lookup_attr_name='image_id',
            list_objs_related_name='images_associations',
            list_serializer=ImageInLineSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_quote_retrieve', methods=('get',))
    @extend_schema(operation_id='word_quote_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_quote_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'quotes/(?P<quote_id>[\w\d-]+)',
        serializer_class=QuoteForWordSerializer,
    )
    def quotes_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить ассоциацию-цитату слова."""
        return self.detail_action(
            request,
            objs_related_name='wordquoteassociations',
            lookup_field='quote__id',
            lookup_attr_name='quote_id',
            list_objs_related_name='quotes_associations',
            list_serializer=QuoteInLineSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='words_favorites_list', methods=('get',))
    @action(detail=False, methods=('get',), permission_classes=(IsAuthenticated,))
    def favorites(self, request):
        """Получить список избранных слов."""
        return self.list(request)

    @extend_schema(operation_id='word_favorite_create', methods=('post',))
    @action(detail=True, methods=('post',), permission_classes=(IsAuthenticated,))
    def favorite(self, request, slug):
        """Добавить слово в избранное."""
        return self._add_to_favorite_action(
            request,
            related_model=FavoriteWord,
            related_model_obj_field='word',
            already_exist_msg='Это слово уже находится в вашем избранном.',
        )

    @extend_schema(operation_id='word_favorite_destroy', methods=('delete',))
    @favorite.mapping.delete
    def remove_from_favorite(self, request, slug):
        """Удалить слово из избранного."""
        return self._remove_from_favorite_action(
            request,
            related_model=FavoriteWord,
            related_model_obj_field='word',
            not_found_msg='Этого слова нет в вашем избранном.',
        )

    @extend_schema(operation_id='images_upload', methods=('post',))
    @action(
        methods=('post',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='images-upload',
        parser_classes=(MultiPartParser, FormParser),
        serializer_class=ImageInLineSerializer,
    )
    def images_upload(self, request, format=None, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['words_translations'])
@extend_schema_view(
    list=extend_schema(operation_id='translations_list'),
    create=extend_schema(operation_id='translations_create'),
    retrieve=extend_schema(operation_id='translation_retrieve'),
    partial_update=extend_schema(operation_id='translation_partial_update'),
    destroy=extend_schema(operation_id='translation_destroy'),
)
class WordTranslationViewSet(
    ActionsWithRelatedWordsMixin,
    ObjectAlreadyExistHandler,
    DestroyReturnListMixin,
    viewsets.ModelViewSet,
):
    """Действия с переводами из своего словаря."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'slug'
    queryset = WordTranslation.objects.none()
    serializer_class = WordTranslationSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering = ('-created',)
    ordering_fields = ('created', 'text', 'words_count')
    search_fields = ('text', 'words__text')

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.wordtranslations.all()
        return None

    def get_serializer_class(self):
        match self.action:
            case 'list' | 'destroy':
                return WordTranslationListSerializer
            case 'create':
                return WordTranslationCreateSerializer
            case _:
                return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        return self.create_return_with_words(
            request, default_order='-wordtranslations__created', *args, **kwargs
        )

    def retrieve(self, request, *args, **kwargs):
        return self.retrieve_with_words(
            request, default_order='-wordtranslations__created', *args, **kwargs
        )

    def partial_update(self, request, *args, **kwargs):
        return self.partial_update_return_with_words(
            request, default_order='-wordtranslations__created', *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_translation', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=WordTranslationSerializer,
    )
    def add_words(self, request, *args, **kwargs):
        """Добавить перевод к словам."""
        return self.add_words_return_with_words(
            request, default_order='-wordtranslations__created', *args, **kwargs
        )


@extend_schema(tags=['usage_examples'])
@extend_schema_view(
    list=extend_schema(operation_id='examples_list'),
    create=extend_schema(operation_id='examples_create'),
    retrieve=extend_schema(operation_id='example_retrieve'),
    partial_update=extend_schema(operation_id='example_partial_update'),
    destroy=extend_schema(operation_id='example_destroy'),
)
class UsageExampleViewSet(
    ActionsWithRelatedWordsMixin,
    ObjectAlreadyExistHandler,
    DestroyReturnListMixin,
    viewsets.ModelViewSet,
):
    """Действия с примерами из своего словаря."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'slug'
    queryset = UsageExample.objects.none()
    serializer_class = UsageExampleSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering = ('-created',)
    ordering_fields = ('created', 'text', 'words_count')
    search_fields = ('text', 'translation', 'words__text')

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.usageexamples.all()
        return None

    def get_serializer_class(self):
        match self.action:
            case 'list' | 'destroy':
                return UsageExampleListSerializer
            case 'create':
                return UsageExampleCreateSerializer
            case _:
                return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        return self.create_return_with_words(
            request, default_order='-wordusageexamples__created', *args, **kwargs
        )

    def retrieve(self, request, *args, **kwargs):
        return self.retrieve_with_words(
            request, default_order='-wordusageexamples__created', *args, **kwargs
        )

    def partial_update(self, request, *args, **kwargs):
        return self.partial_update_return_with_words(
            request, default_order='-wordusageexamples__created', *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_example', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=UsageExampleSerializer,
    )
    def add_words(self, request, *args, **kwargs):
        """Добавить пример к словам."""
        return self.add_words_return_with_words(
            request, default_order='-wordusageexamples__created', *args, **kwargs
        )


@extend_schema(tags=['definitions'])
@extend_schema_view(
    list=extend_schema(operation_id='definitions_list'),
    create=extend_schema(operation_id='definitions_create'),
    retrieve=extend_schema(operation_id='definition_retrieve'),
    partial_update=extend_schema(operation_id='definition_partial_update'),
    destroy=extend_schema(operation_id='definition_destroy'),
)
class DefinitionViewSet(
    ActionsWithRelatedWordsMixin,
    ObjectAlreadyExistHandler,
    DestroyReturnListMixin,
    viewsets.ModelViewSet,
):
    """Действия с определениями из своего словаря."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'slug'
    queryset = Definition.objects.none()
    serializer_class = DefinitionSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering = ('-created',)
    ordering_fields = ('created', 'text', 'words_count')
    search_fields = ('text', 'translation', 'words__text')

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.definitions.all()
        return None

    def get_serializer_class(self):
        match self.action:
            case 'list' | 'destroy':
                return DefinitionListSerializer
            case 'create':
                return DefinitionCreateSerializer
            case _:
                return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        return self.create_return_with_words(
            request, default_order='-worddefinitions__created', *args, **kwargs
        )

    def retrieve(self, request, *args, **kwargs):
        return self.retrieve_with_words(
            request, default_order='-worddefinitions__created', *args, **kwargs
        )

    def partial_update(self, request, *args, **kwargs):
        return self.partial_update_return_with_words(
            request, default_order='-worddefinitions__created', *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_definition', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=DefinitionSerializer,
    )
    def add_words(self, request, *args, **kwargs):
        """Добавить определение к словам."""
        return self.add_words_return_with_words(
            request, default_order='-worddefinitions__created', *args, **kwargs
        )


@extend_schema(tags=['associations'])
@extend_schema_view(
    list=extend_schema(operation_id='associations_list'),
)
class AssociationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Получить список всех ассоциаций из своего словаря."""

    http_method_names = ('get',)
    queryset = ImageAssociation.objects.none()
    serializer_class = ImageShortSerailizer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination

    def list(self, request, *args, **kwargs):
        user = request.user
        images = ImageInLineSerializer(
            user.imageassociations.all(),
            many=True,
            context={'request': request},
        )
        quotes = QuoteInLineSerializer(
            user.quoteassociations.all(),
            many=True,
            context={'request': request},
        )
        result_list = sorted(
            chain(quotes.data, images.data),
            key=lambda d: d.get('created'),
            reverse=True,
        )
        return Response(result_list)


@extend_schema(tags=['images_associations'])
@extend_schema_view(
    list=extend_schema(operation_id='images_list'),
    retrieve=extend_schema(operation_id='image_retrieve'),
    partial_update=extend_schema(operation_id='image_partial_update'),
    destroy=extend_schema(operation_id='image_destroy'),
)
class ImageViewSet(
    ActionsWithRelatedWordsMixin,
    DestroyReturnListMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Действия с ассоциациями-картинками из своего словаря."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'id'
    queryset = ImageAssociation.objects.none()
    serializer_class = ImageInLineSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering = ('-created',)
    ordering_fields = ('created', 'name', 'words_count')
    search_fields = ('name', 'words__text')

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.imageassociations.all()
        return None

    def get_serializer_class(self):
        match self.action:
            case 'list' | 'destroy':
                return ImageListSerializer
            case _:
                return super().get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        return self.retrieve_with_words(
            request, default_order='-wordimageassociations__created', *args, **kwargs
        )

    def partial_update(self, request, *args, **kwargs):
        return self.partial_update_return_with_words(
            request, default_order='-wordimageassociations__created', *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_image', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=ImageInLineSerializer,
    )
    def add_words(self, request, *args, **kwargs):
        """Добавить ассоциацию-картинку к словам."""
        return self.add_words_return_with_words(
            request, default_order='-wordimageassociations__created', *args, **kwargs
        )


@extend_schema(tags=['quotes_associations'])
@extend_schema_view(
    retrieve=extend_schema(operation_id='quote_retrieve'),
    partial_update=extend_schema(operation_id='quote_partial_update'),
    destroy=extend_schema(operation_id='quote_destroy'),
)
class QuoteViewSet(
    ActionsWithRelatedWordsMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Действия с ассоциациями-цитатами из своего словаря."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'id'
    queryset = QuoteAssociation.objects.none()
    serializer_class = QuoteInLineSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering = ('-created',)
    ordering_fields = ('created', 'text', 'words_count')
    search_fields = ('text', 'quote_author', 'words__text')

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.quoteassociations.all()
        return None

    def retrieve(self, request, *args, **kwargs):
        return self.retrieve_with_words(
            request, default_order='-wordquoteassociations__created', *args, **kwargs
        )

    def partial_update(self, request, *args, **kwargs):
        return self.partial_update_return_with_words(
            request, default_order='-wordquoteassociations__created', *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_quote', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=QuoteInLineSerializer,
    )
    def add_words(self, request, *args, **kwargs):
        """Добавить ассоциацию-цитату к словам."""
        return self.add_words_return_with_words(
            request, default_order='-wordquoteassociations__created', *args, **kwargs
        )


@extend_schema(tags=['synonyms'])
@extend_schema_view(
    retrieve=extend_schema(operation_id='synonym_retrieve'),
    partial_update=extend_schema(operation_id='synonym_partial_update'),
    destroy=extend_schema(operation_id='synonym_destroy'),
)
class SynonymViewSet(
    ActionsWithRelatedWordsMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Действия с синонимами из своего словаря."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'slug'
    queryset = Word.objects.none()
    serializer_class = SynonymSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering = ('-created',)
    ordering_fields = ('created', 'text', 'words_count')
    search_fields = ('text', 'words__text')

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.words.filter(synonyms__isnull=False).distinct()
        return None

    def get_serializer_class(self):
        match self.action:
            case 'partial_update':
                return WordSerializer
            case _:
                return super().get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        return self.retrieve_with_words(
            request,
            default_order='-synonym_to_words__created',
            words_related_name='synonyms',
            *args,
            **kwargs,
        )

    def partial_update(self, request, *args, **kwargs):
        return self.partial_update_return_with_words(
            request,
            default_order='-synonym_to_words__created',
            words_related_name='synonyms',
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='words_add_to_synonym', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=SynonymSerializer,
    )
    def add_words(self, request, *args, **kwargs):
        """Добавить синоним к словам."""
        return self.add_words_return_with_words(
            request,
            default_order='-synonym_to_words__created',
            words_related_name='synonyms',
            *args,
            **kwargs,
        )


@extend_schema(tags=['antonyms'])
@extend_schema_view(
    retrieve=extend_schema(operation_id='antonym_retrieve'),
    partial_update=extend_schema(operation_id='antonym_partial_update'),
    destroy=extend_schema(operation_id='antonym_destroy'),
)
class AntonymViewSet(
    ActionsWithRelatedWordsMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Действия с антонимами из своего словаря."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'slug'
    queryset = Word.objects.none()
    serializer_class = AntonymSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering = ('-created',)
    ordering_fields = ('created', 'text', 'words_count')
    search_fields = ('text', 'words__text')

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.words.filter(antonyms__isnull=False).distinct()
        return None

    def get_serializer_class(self):
        match self.action:
            case 'partial_update':
                return WordSerializer
            case _:
                return super().get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        return self.retrieve_with_words(
            request,
            default_order='-antonym_to_words__created',
            words_related_name='antonyms',
            *args,
            **kwargs,
        )

    def partial_update(self, request, *args, **kwargs):
        return self.partial_update_return_with_words(
            request,
            default_order='-antonym_to_words__created',
            words_related_name='antonyms',
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='words_add_to_antonym', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=AntonymSerializer,
    )
    def add_words(self, request, *args, **kwargs):
        """Добавить антоним к словам."""
        return self.add_words_return_with_words(
            request,
            default_order='-antonym_to_words__created',
            words_related_name='antonyms',
            *args,
            **kwargs,
        )


@extend_schema(tags=['similars'])
@extend_schema_view(
    retrieve=extend_schema(operation_id='similar_retrieve'),
    partial_update=extend_schema(operation_id='similar_partial_update'),
    destroy=extend_schema(operation_id='similar_destroy'),
)
class SimilarViewSet(
    ActionsWithRelatedWordsMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Действия с похожими словами из своего словаря."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'slug'
    queryset = Word.objects.none()
    serializer_class = SimilarSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering = ('-created',)
    ordering_fields = ('created', 'text', 'words_count')
    search_fields = ('text', 'words__text')

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.words.filter(similars__isnull=False).distinct()
        return None

    def get_serializer_class(self):
        match self.action:
            case 'partial_update':
                return WordSerializer
            case _:
                return super().get_serializer_class()

    def retrieve(self, request, *args, **kwargs):
        return self.retrieve_with_words(
            request,
            default_order='-similar_to_words__created',
            words_related_name='similars',
            *args,
            **kwargs,
        )

    def partial_update(self, request, *args, **kwargs):
        return self.partial_update_return_with_words(
            request,
            default_order='-similar_to_words__created',
            words_related_name='similars',
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='words_add_to_similar', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=SimilarSerializer,
    )
    def add_words(self, request, *args, **kwargs):
        """Добавить похожие слова."""
        return self.add_words_return_with_words(
            request,
            default_order='-similar_to_words__created',
            words_related_name='similars',
            *args,
            **kwargs,
        )


@extend_schema(tags=['tags'])
@extend_schema_view(list=extend_schema(operation_id='user_tags_list'))
class TagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.none()
    serializer_class = TagListSerializer
    http_method_names = ('get',)
    pagination_class = None
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering = ('-words_count', '-created')

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return user.tags.annotate(words_count=Count('words', distinct=True))
        return Tag.objects.none()


@extend_schema(tags=['types'])
@extend_schema_view(list=extend_schema(operation_id='types_list'))
class TypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Просмотр списка всех возможных типов слов и фраз."""

    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    lookup_field = 'slug'
    http_method_names = ('get',)
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering = ('-words_count',)

    def get_queryset(self):
        return Type.objects.annotate(words_count=Count('words', distinct=True))


@extend_schema(tags=['forms groups'])
@extend_schema_view(
    list=extend_schema(operation_id='formsgroups_list'),
)
class FormsGroupsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Просмотр списка всех групп форм пользователя."""

    serializer_class = FormsGroupListSerializer
    lookup_field = 'slug'
    http_method_names = ('get',)
    permission_classes = (IsAuthenticated,)
    queryset = FormsGroup.objects.none()
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)

    def get_queryset(self):
        user = self.request.user
        admin_user = User.objects.filter(username='admin').first()
        if admin_user and user.is_authenticated:
            return FormsGroup.objects.filter(
                Q(author=user) | Q(author=admin_user)
            ).annotate(words_count=Count('words', distinct=True))
        elif user.is_authenticated:
            return FormsGroup.objects.filter(author=user).annotate(
                words_count=Count('words', distinct=True)
            )
        return FormsGroup.objects.none()


@extend_schema(tags=['collections'])
@extend_schema_view(
    list=extend_schema(operation_id='collections_list'),
    create=extend_schema(operation_id='collection_create'),
    retrieve=extend_schema(operation_id='collection_retrieve'),
    partial_update=extend_schema(operation_id='collection_partial_update'),
    destroy=extend_schema(operation_id='collection_destroy'),
)
class CollectionViewSet(
    ActionsWithRelatedWordsMixin,
    ObjectAlreadyExistHandler,
    DestroyReturnListMixin,
    FavoriteMixin,
    viewsets.ModelViewSet,
):
    """Действия с коллекциями."""

    lookup_field = 'slug'
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)
    queryset = Collection.objects.none()
    serializer_class = CollectionSerializer
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
            case 'list' | 'favorites' | 'destroy':
                return CollectionShortSerializer
            case _:
                return super().get_serializer_class()

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

    def create(self, request, *args, **kwargs):
        return self.create_return_with_words(
            request, default_order='-wordsincollections__created', *args, **kwargs
        )

    def retrieve(self, request, *args, **kwargs):
        return self.retrieve_with_words(
            request, default_order='-wordsincollections__created', *args, **kwargs
        )

    def partial_update(self, request, *args, **kwargs):
        return self.partial_update_return_with_words(
            request, default_order='-wordsincollections__created', *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_collection', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=CollectionSerializer,
    )
    def add_words(self, request, *args, **kwargs):
        """Добавить слова в коллекцию."""
        return self.add_words_return_with_words(
            request, default_order='-wordsincollections__created', *args, **kwargs
        )

    def retrieve_words_objs(
        self,
        request,
        objs_response_name,
        objs_model,
        objs_viewset,
        objs_list_serializer,
        *args,
        **kwargs,
    ):
        queryset = self.get_queryset()
        collection = get_object_or_404(
            queryset, **{self.lookup_field: self.kwargs[self.lookup_field]}
        )
        response_data = self.get_serializer(collection).data
        _objs = (
            objs_model.objects.filter(words__in=collection.words.all())
            .distinct()
            .annotate(words_count=Count('words'))
        )
        objs_data = self.get_filtered_paginated_objs(
            request, _objs, objs_viewset, objs_list_serializer
        )
        return Response(
            {
                **response_data,
                objs_response_name: objs_data,
            }
        )

    @extend_schema(operation_id='collection_images_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=CollectionSerializer,
    )
    def images(self, request, *args, **kwargs):
        """Получить все картинки слов коллекции."""
        return self.retrieve_words_objs(
            request,
            'images_associations',
            ImageAssociation,
            ImageViewSet,
            ImageListSerializer,
        )

    @extend_schema(operation_id='collection_translations_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=CollectionSerializer,
    )
    def translations(self, request, *args, **kwargs):
        """Получить все переводы слов коллекции."""
        return self.retrieve_words_objs(
            request,
            'translations',
            WordTranslation,
            WordTranslationViewSet,
            WordTranslationListSerializer,
        )

    @extend_schema(operation_id='collection_definitions_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=CollectionSerializer,
    )
    def definitions(self, request, *args, **kwargs):
        """Получить все определения слов коллекции."""
        return self.retrieve_words_objs(
            request,
            'definitions',
            Definition,
            DefinitionViewSet,
            DefinitionListSerializer,
        )

    @extend_schema(operation_id='collection_examples_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=CollectionSerializer,
    )
    def examples(self, request, *args, **kwargs):
        """Получить все примеры слов коллекции."""
        return self.retrieve_words_objs(
            request,
            'examples',
            UsageExample,
            UsageExampleViewSet,
            UsageExampleListSerializer,
        )

    @extend_schema(operation_id='collections_favorites_list', methods=('get',))
    @action(detail=False, methods=('get',), permission_classes=(IsAuthenticated,))
    def favorites(self, request):
        """Получить список избранных коллекций."""
        return self.list(request)

    @extend_schema(operation_id='collection_favorite_create', methods=('post',))
    @action(detail=True, methods=('post',), permission_classes=(IsAuthenticated,))
    def favorite(self, request, slug):
        """Добавить коллекцию в избранное."""
        return self._add_to_favorite_action(
            request,
            related_model=FavoriteCollection,
            related_model_obj_field='collection',
            already_exist_msg='Эта коллекция уже находится в вашем избранном.',
        )

    @extend_schema(operation_id='collection_favorite_destroy', methods=('delete',))
    @favorite.mapping.delete
    def remove_from_favorite(self, request, slug):
        """Удалить коллекцию из избранного."""
        return self._remove_from_favorite_action(
            request,
            related_model=FavoriteCollection,
            related_model_obj_field='collection',
            not_found_msg='Этой коллекции нет в вашем избранном.',
        )

    @extend_schema(operation_id='add_words_to_collections', methods=('post',))
    @action(
        methods=('post',),
        detail=False,
        url_path='add-words-to-collections',
        serializer_class=CollectionShortSerializer,
    )
    def add_words_to_collections(self, request, *args, **kwargs):
        """Добавить выбранные слова в выбранные коллекции."""
        serializer = MultipleWordsSerializer(
            data=request.data, many=False, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        try:
            self.perform_create(serializer)
            words_added_count = len(serializer.validated_data['words'])
            collections_count = len(serializer.validated_data['collections'])
            headers = self.get_success_headers(serializer.data)
            response_data = self.list(request).data
            return Response(
                {
                    **response_data,
                    'words_added_count': words_added_count,
                    'collections_count': collections_count,
                },
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        except ObjectAlreadyExist as exception:
            return exception.get_detail_response(request)


@extend_schema(tags=['languages'])
@extend_schema_view(
    list=extend_schema(operation_id='learning_languages_list'),
    create=extend_schema(operation_id='learning_language_create'),
    retrieve=extend_schema(operation_id='learning_language_retrieve'),
    destroy=extend_schema(operation_id='learning_language_destroy'),
)
class LanguagesViewSet(ActionsWithRelatedObjectsMixin, viewsets.ModelViewSet):
    """Действия с изучаемыми и родными языками."""

    http_method_names = ('get', 'post', 'delete')
    lookup_field = 'slug'
    queryset = UserLearningLanguage.objects.none()
    serializer_class = LearningLanguageSerailizer
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    filter_backends = (
        filters.OrderingFilter,
        DjangoFilterBackend,
    )
    ordering = ('-words_count',)

    def get_queryset(self):
        user = self.request.user
        match self.action:
            case 'native' | 'add_native_languages':
                return user.native_languages_detail.annotate(
                    words_count=Count(
                        'user__wordtranslations',
                        filter=Q(user__wordtranslations__language=F('language')),
                    )
                )
            case 'all':
                return Language.objects.annotate(words_count=Count('words'))
            case 'available':
                return Language.objects.filter(learning_available=True).annotate(
                    words_count=Count('words')
                )
            case 'interface':
                return Language.objects.filter(interface_available=True).annotate(
                    words_count=Count('words')
                )
            case _:
                return user.learning_languages_detail.annotate(
                    words_count=Count(
                        'user__words', filter=Q(user__words__language=F('language'))
                    )
                )

    def get_serializer_class(self):
        match self.action:
            case 'list' | 'destroy':
                return LearningLanguageWithLastWordsSerailizer
            case _:
                return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        response_data = super().list(request, *args, **kwargs).data
        return Response({'count': len(response_data), 'results': response_data})

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data, many=True)
            serializer.is_valid(raise_exception=True)
            amount_limit = kwargs.get(
                'amount_limit', UsersAmountLimits.MAX_LEARNING_LANGUAGES_AMOUNT
            )
            if (
                request.user.learning_languages.count() + len(serializer.validated_data)
                > amount_limit
            ):
                return Response(
                    {'detail': UsersAmountLimits.get_error_message(limit=amount_limit)},
                    status=status.HTTP_409_CONFLICT,
                )
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            list_response_data = self.list(request).data
            return Response(
                list_response_data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        except IntegrityError:
            return Response(
                {
                    'detail': _(
                        kwargs.get(
                            'integrityerror_detail',
                            'Этот язык уже добавлен в изучаемые.',
                        )
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

    def retrieve(self, request, *args, **kwargs):
        instance = kwargs.get('instance', self.get_object())
        response_data = self.get_serializer(instance).data
        _words = instance.user.words.filter(language=instance.language).annotate(
            translations_count=Count('translations', distinct=True),
            examples_count=Count('examples', distinct=True),
            collections_count=Count('collections', distinct=True),
        )
        words_serializer = get_words_view(request)
        words_data = self.get_filtered_paginated_objs(
            request, _words, WordViewSet, words_serializer
        )
        return Response(
            {
                **response_data,
                'words': words_data,
            }
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user.words.filter(language=instance.language).exists():
            return Response(
                {
                    'detail': _(
                        'Нельзя удалить язык из изучаемых, если в вашем словаре '
                        'есть слова на этом языке.'
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(operation_id='language_collections_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        permission_classes=(IsAuthenticated,),
        serializer_class=LearningLanguageSerailizer,
    )
    def collections(self, request, *args, **kwargs):
        instance = self.get_object()
        response_data = self.get_serializer(instance).data
        _collections = instance.user.collections.filter(
            words__language=instance.language
        )
        collections_data = self.get_filtered_paginated_objs(
            request, _collections, CollectionViewSet, CollectionShortSerializer
        )
        return Response(
            {
                **response_data,
                'collections': collections_data,
            }
        )

    @extend_schema(operation_id='native_languages_list', methods=('get',))
    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        serializer_class=NativeLanguageSerailizer,
    )
    def native(self, request, *args, **kwargs):
        return self.list(request)

    @extend_schema(operation_id='native_language_create', methods=('post',))
    @native.mapping.post
    def add_native_languages(self, request, *args, **kwargs):
        return self.create(
            request,
            integrityerror_detail='Этот язык уже добавлен в родные.',
            amount_limit=UsersAmountLimits.MAX_NATIVE_LANGUAGES_AMOUNT,
        )

    @extend_schema(operation_id='all_languages_list', methods=('get',))
    @action(
        methods=('get',),
        detail=False,
        serializer_class=LanguageSerailizer,
        permission_classes=(AllowAny,),
        pagination_class=LimitPagination,
    )
    def all(self, request, *args, **kwargs):
        return super().list(request)

    @extend_schema(
        operation_id='languages_available_for_learning_list', methods=('get',)
    )
    @action(
        methods=('get',),
        detail=False,
        serializer_class=LanguageSerailizer,
        permission_classes=(AllowAny,),
    )
    def available(self, request, *args, **kwargs):
        return self.list(request)

    @extend_schema(
        operation_id='learning_and_available_languages_list', methods=('get',)
    )
    @action(
        methods=('get',),
        detail=False,
        url_path='learning-available',
        serializer_class=LearningLanguageShortSerailizer,
        permission_classes=(IsAuthenticated,),
    )
    def learning_available(self, request, *args, **kwargs):
        learning_data = self.list(request).data
        serializer = LanguageSerailizer(
            Language.objects.filter(learning_available=True), many=True
        )
        return Response(
            {
                'learning': learning_data,
                'available': {
                    'count': len(serializer.data),
                    'results': serializer.data,
                },
            }
        )

    @extend_schema(operation_id='interface_switch_languages_list', methods=('get',))
    @action(
        methods=('get',),
        detail=False,
        serializer_class=LanguageSerailizer,
        permission_classes=(AllowAny,),
    )
    def interface(self, request, *args, **kwargs):
        return self.list(request)

    @extend_schema(operation_id='language_images_choice_retrieve', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        url_path='images-choice',
        serializer_class=LearningLanguageSerailizer,
        permission_classes=(IsAuthenticated,),
    )
    def images_choice(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ImageShortSerailizer(
            instance.language.images.all(),
            many=True,
            context=self.context,
        )
        return Response(serializer.data)

    @extend_schema(operation_id='language_image_update', methods=('post',))
    @images_choice.mapping.post
    def update_language_image(self, request, *args, **kwargs):
        instance = self.get_object()
        image_id = request.data.get('id', None)
        if image_id:
            image = get_object_or_404(instance.language.images.all(), id=image_id).image
            instance.image = image
            instance.save()
        return self.retrieve(request, instance=instance)


@extend_schema(tags=['main_page'])
@extend_schema_view(
    list=extend_schema(operation_id='main_page_retrieve'),
)
class MainPageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    http_method_names = ('get',)
    lookup_field = 'slug'
    queryset = User.objects.none()
    serializer_class = MainPageSerailizer
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, many=False)
        return Response(serializer.data)
