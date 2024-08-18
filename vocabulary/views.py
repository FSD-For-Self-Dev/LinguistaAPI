"""Vocabulary views."""

import random
import logging
from itertools import chain

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q, F, Model
from django.db.models.query import QuerySet
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.http import HttpRequest, HttpResponse

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
from rest_framework.serializers import Serializer
from rest_framework.exceptions import NotFound

from core.pagination import LimitPagination
from core.exceptions import (
    AmountLimitExceeded,
    ObjectAlreadyExist,
)
from core.mixins import (
    ActionsWithRelatedObjectsMixin,
    AmountLimitExceededHandler,
    ObjectAlreadyExistHandler,
    DestroyReturnListMixin,
    FavoriteMixin,
)
from core.utils import get_admin_user, check_amount_limit
from languages.serializers import LanguageSerializer
from users.models import (
    UserDefaultWordsView,
    UserLearningLanguage,
    UserNativeLanguage,
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
    ImageAssociation,
    QuoteAssociation,
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
    WordTranslationSerializer,
    WordTranslationCreateSerializer,
    WordTranslationListSerializer,
    UsageExampleInLineSerializer,
    UsageExampleSerializer,
    UsageExampleCreateSerializer,
    UsageExampleListSerializer,
    DefinitionInLineSerializer,
    DefinitionSerializer,
    DefinitionCreateSerializer,
    DefinitionListSerializer,
    SynonymForWordListSerializer,
    SynonymInLineSerializer,
    SynonymSerializer,
    AntonymForWordListSerializer,
    AntonymInLineSerializer,
    AntonymSerializer,
    FormForWordListSerializer,
    FormInLineSerializer,
    SimilarForWordListSerializer,
    SimilarInLineSerializer,
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
    LanguageImageSerailizer,
    QuoteInLineSerializer,
    AssociationsCreateSerializer,
    LearningLanguageWithLastWordsSerailizer,
    MainPageSerailizer,
    AllUserAssociationsSerializer,
    CoverSetSerailizer,
)

logger = logging.getLogger(__name__)

User = get_user_model()


def get_words_view(request: HttpRequest) -> Serializer:
    """Returns serializer class for words list."""
    words_view = {
        'standart': WordStandartCardSerializer,
        'short': WordShortCardSerializer,
        'long': WordLongCardSerializer,
    }
    default_words_view = 'standart'

    # Return serializer class based on `words_view_param` query parameter if passed
    # or try to get user setting for default word cards view from database
    # or return serializer class defined in `default_words_view`
    words_view_param = request.query_params.get('view', None)
    logger.debug(f'Word cards view query parameter passed: {words_view_param}')

    if not words_view_param:
        try:
            words_view_param = UserDefaultWordsView.objects.get(
                user=request.user
            ).words_view
            logger.debug(
                f'Word cards view parameter obtained from users default settings: '
                f'{words_view_param}'
            )
        except Exception:
            words_view_param = default_words_view
            logger.debug(
                f'Word cards view parameter is set to default: {words_view_param}'
            )

    return words_view.get(words_view_param)


def annotate_words_with_counters(
    words: QuerySet[Word] | None = None,
    instance: Model | None = None,
    words_related_name: str = '',
    ordering: list[str] = [],
) -> QuerySet[Word]:
    """
    Annotates words with some related objects amount to use in filters, sorting.

    Args:
        words (QuerySet): words queryset to be annotated.
        instance (Model subclass): instance to obtain words from if words not passed.
        words_related_name (str): related name to obtain words by if words not passed.
        ordering (list[str]): list of fields to be sorted words by.
    """
    if words is None:
        return (
            instance.__getattribute__(words_related_name)
            .annotate(
                translations_count=Count('translations', distinct=True),
                examples_count=Count('examples', distinct=True),
                collections_count=Count('collections', distinct=True),
            )
            .order_by(*ordering)
        )

    return words.annotate(
        translations_count=Count('translations', distinct=True),
        examples_count=Count('examples', distinct=True),
        collections_count=Count('collections', distinct=True),
    ).order_by(*ordering)


class ActionsWithRelatedWordsMixin(ActionsWithRelatedObjectsMixin):
    """Custom mixin to add related words data to response."""

    def retrieve_with_words(
        self,
        request: HttpRequest,
        default_order: list[str] = ['-created'],
        words_related_name: str = 'words',
        words: QuerySet[Word] | None = None,
        *args,
        **kwargs,
    ) -> HttpResponse:
        """
        Returns instance data with related words filtered, paginated, ordered data.

        Args:
            default_order (list[str]): list of fields to be sorted words by.
            words_related_name (str): related name to obtain words by if words not
                                      passed.
            words (QuerySet): related words queryset.
        """
        queryset = self.get_queryset()
        instance = get_object_or_404(
            queryset, **{self.lookup_field: self.kwargs[self.lookup_field]}
        )
        logger.debug(f'Obtained instance: {instance}')

        instance_data = self.get_serializer(instance).data

        # Obtaining words from instance if words not passed,
        # annotate words with counters
        _words = (
            annotate_words_with_counters(
                instance=instance,
                words_related_name=words_related_name,
                ordering=default_order,
            )
            if words is None
            else annotate_words_with_counters(words, ordering=default_order)
        )
        logger.debug(f'Obtained words: {_words}')

        words_serializer_class = get_words_view(request)
        logger.debug(f'Serializer used for words: {words_serializer_class}')

        words_data = self.get_filtered_paginated_objs(
            request, _words, WordViewSet, words_serializer_class
        )

        return Response(
            {
                **instance_data,
                'words': words_data,
            }
        )

    def create_return_with_words(
        self,
        request: HttpRequest,
        default_order: list[str] = ['-created'],
        words_related_name: str = 'words',
        *args,
        **kwargs,
    ) -> HttpResponse:
        """
        Returns created instance data with related words filtered, paginated,
        ordered data.

        Args:
            default_order (list[str]): list of fields to be sorted words by.
            words_related_name (str): related name to obtain words by.

        """
        serializer = self.get_serializer(data=request.data)
        logger.debug(f'Serializer used for instance: {type(serializer)}')

        logger.debug('Validating data')
        serializer.is_valid(raise_exception=True)

        logger.debug('Performing instance save')
        instance = serializer.save()

        _words = annotate_words_with_counters(
            instance=instance,
            words_related_name=words_related_name,
            ordering=default_order,
        )
        logger.debug(f'Obtained words: {_words}')

        words_serializer_class = get_words_view(request)
        logger.debug(f'Serializer used for words: {words_serializer_class}')

        words_data = self.paginate_related_objs(request, _words, words_serializer_class)

        return Response(
            {
                **serializer.data,
                'words': words_data,
            },
            status=status.HTTP_201_CREATED,
        )

    def partial_update_return_with_words(
        self,
        request: HttpRequest,
        default_order: list[str] = ['-created'],
        words_related_name: str = 'words',
        *args,
        **kwargs,
    ) -> HttpResponse:
        """
        Returns updated instance data with related words filtered, paginated,
        ordered data.

        Args:
            default_order (list[str]): list of fields to be sorted words by.
            words_related_name (str): related name to obtain words by.
        """
        instance = self.get_object()
        logger.debug(f'Obtained instance: {instance}')

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        logger.debug(f'Serializer used for instance: {type(serializer)}')

        logger.debug('Validating data')
        serializer.is_valid(raise_exception=True)

        logger.debug('Performing update')
        self.perform_update(serializer)

        _words = annotate_words_with_counters(
            instance=instance,
            words_related_name=words_related_name,
            ordering=default_order,
        )
        logger.debug(f'Obtained words: {_words}')

        words_serializer_class = get_words_view(request)
        logger.debug(f'Serializer used for words: {words_serializer_class}')

        words_data = self.paginate_related_objs(request, _words, words_serializer_class)

        return Response(
            {
                **serializer.data,
                'words': words_data,
            }
        )

    def add_words_return_retrieve_with_words(
        self,
        request: HttpRequest,
        default_order: list[str] = ['-created'],
        words_related_name: str = 'words',
        *args,
        **kwargs,
    ) -> HttpResponse:
        """
        Adds passed words to instance, returns updated instance data with
        related words filtered, paginated, ordered data.

        Args:
            default_order (list[str]): list of fields to be sorted words by.
            words_related_name (str): related name to obtain words by.
        """
        instance = self.get_object()
        logger.debug(f'Obtained instance: {instance}')

        instance_data = self.create_related_objs(
            request,
            objs_related_name=words_related_name,
            serializer_class=WordShortCreateSerializer,
            set_objs=True,
            instance=instance,
        ).data

        _words = annotate_words_with_counters(
            instance=instance,
            words_related_name=words_related_name,
            ordering=default_order,
        )
        logger.debug(f'Obtained words: {_words}')

        words_serializer_class = get_words_view(request)
        logger.debug(f'Serializer used for words: {words_serializer_class}')

        words_data = self.paginate_related_objs(request, _words, words_serializer_class)

        return Response(
            {
                **instance_data,
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
    AmountLimitExceededHandler,
    ObjectAlreadyExistHandler,
    DestroyReturnListMixin,
    FavoriteMixin,
    viewsets.ModelViewSet,
):
    """Words CRUD and actions with word related objects."""

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

    def get_queryset(self) -> QuerySet[Word]:
        """Returns all words from user vocabulary or favorites only."""
        user = self.request.user
        if user.is_authenticated:
            match self.action:
                case 'favorites':
                    return Word.objects.filter(favorite_for__user=user).order_by(
                        '-favorite_for__created'
                    )
                case _:
                    # Annotate words with some related objects amount to use in
                    # filters, sorting
                    return annotate_words_with_counters(
                        instance=user, words_related_name='words'
                    )
        return Word.objects.none()

    def get_serializer_class(self) -> Serializer:
        match self.action:
            case 'list' | 'destroy' | 'multiple_create' | 'favorites':
                return get_words_view(self.request)
            case 'notes_create':
                return NoteForWordSerializer
            case _:
                return super().get_serializer_class()

    @extend_schema(operation_id='word_random')
    @action(
        methods=('get',),
        detail=False,
        serializer_class=WordStandartCardSerializer,
    )
    def random(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Return one random word from user's vocabulary."""
        queryset = self.filter_queryset(self.get_queryset())
        word: Word | None = random.choice(queryset) if queryset else None
        logger.debug(f'Random word from {request.user} user vocabulary: {word}')
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
    def problematic(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Switch value for `is_problematic` word mark."""
        word: Word = self.get_object()
        logger.debug(f'Old value: {word.is_problematic}')

        word.is_problematic = not word.is_problematic
        word.save()
        logger.debug(f'New value: {word.is_problematic}')

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
    def multiple_create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Creates multiple words at time, adds given words to given collections."""
        serializer = MultipleWordsSerializer(
            data=request.data, many=False, context={'request': request}
        )
        logger.debug(f'Serializer used: {type(serializer)}')

        logger.debug(f'Validating data: {request.data}')
        serializer.is_valid(raise_exception=True)

        try:
            logger.debug('Performing create')
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
            logger.error(f'ObjectAlreadyExist exception occured: {exception}')
            return exception.get_detail_response(request)

        except NotFound as exception:
            logger.error(f'ObjectDoesNotExist exception occured: {exception}')
            raise exception

    @extend_schema(operation_id='word_tags_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=TagListSerializer,
    )
    def tags(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all tags for given word."""
        return self.list_related_objs(request, objs_related_name='tags')

    @extend_schema(operation_id='word_collections_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=CollectionShortSerializer,
    )
    def collections(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all collections with given word."""
        return self.list_related_objs(request, objs_related_name='collections')

    @extend_schema(operation_id='word_collections_add', methods=('post',))
    @collections.mapping.post
    def collections_add(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds given word to passed collections."""
        return self.create_related_objs(
            request,
            objs_related_name='collections',
            set_objs=True,
            response_serializer_class=WordSerializer,
        )

    @extend_schema(operation_id='word_translations_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=WordTranslationInLineSerializer,
    )
    def translations(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all translations for given word."""
        queryset = self.get_queryset()
        instance = get_object_or_404(
            queryset, **{self.lookup_field: self.kwargs[self.lookup_field]}
        )
        logger.debug(f'Word instance: {instance}')

        filterby_language_name = request.query_params.get('language', '')
        logger.debug(
            f'Language name query param to filter translations: '
            f'{filterby_language_name}'
        )

        _objs = (
            instance.translations.filter(language__name=filterby_language_name)
            if filterby_language_name
            else instance.translations.all()
        )
        logger.debug(f'Obtained objects: {_objs}')

        translations_languages = instance.translations.values_list(
            'language__name', flat=True
        )
        logger.debug(f'Translations languages list: {translations_languages}')

        return self.list_related_objs(
            request,
            objs_related_name='translations',
            objs=_objs,
            response_extra_data={'languages': translations_languages},
        )

    @extend_schema(operation_id='word_translations_create', methods=('post',))
    @translations.mapping.post
    def translations_create(
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        """Adds new translations for given word."""
        return self.create_related_objs(
            request,
            objs_related_name='translations',
            amount_limit=VocabularyAmountLimits.MAX_TRANSLATIONS_AMOUNT,
            amount_limit_exceeded_detail=VocabularyAmountLimits.Details.TRANSLATIONS_AMOUNT_EXCEEDED,
            set_objs=True,
            response_serializer_class=WordSerializer,
        )

    @extend_schema(operation_id='word_translations_retrieve', methods=('get',))
    @extend_schema(operation_id='word_translation_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_translation_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'translations/(?P<translation_slug>[\w-]+)',
        serializer_class=WordTranslationInLineSerializer,
    )
    def translations_detail(
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        """Retrieve, update, disassociate translation for given word."""
        return self.detail_action(
            request,
            objs_related_name='translations',
            lookup_field='slug',
            lookup_query_param='translation_slug',
            delete_through_manager=True,
            response_objs_name='translations',
            response_serializer_class=WordTranslationInLineSerializer,
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
    def definitions(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all definitions for given word."""
        return self.list_related_objs(request, objs_related_name='definitions')

    @extend_schema(operation_id='word_definitions_create', methods=('post',))
    @definitions.mapping.post
    def definitions_create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds new definitions for given word."""
        return self.create_related_objs(
            request,
            objs_related_name='definitions',
            amount_limit=VocabularyAmountLimits.MAX_DEFINITIONS_AMOUNT,
            amount_limit_exceeded_detail=VocabularyAmountLimits.Details.DEFINITIONS_AMOUNT_EXCEEDED,
            set_objs=True,
            response_serializer_class=WordSerializer,
        )

    @extend_schema(operation_id='word_definition_retrieve', methods=('get',))
    @extend_schema(operation_id='word_definition_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_definition_destroy', methods=('delete',))
    @action(
        detail=True,
        methods=('get', 'patch', 'delete'),
        url_path=r'definitions/(?P<definition_slug>[\w-]+)',
        serializer_class=DefinitionInLineSerializer,
    )
    def definitions_detail(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Retrieve, update, disassociate definition for given word."""
        return self.detail_action(
            request,
            objs_related_name='definitions',
            lookup_field='slug',
            lookup_query_param='definition_slug',
            delete_through_manager=True,
            response_objs_name='definitions',
            response_serializer_class=DefinitionInLineSerializer,
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
    def examples(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all usage examples for given word."""
        return self.list_related_objs(request, objs_related_name='examples')

    @extend_schema(operation_id='word_examples_create', methods=('post',))
    @examples.mapping.post
    def examples_create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds new usage examples for given word."""
        return self.create_related_objs(
            request,
            objs_related_name='examples',
            amount_limit=VocabularyAmountLimits.MAX_EXAMPLES_AMOUNT,
            amount_limit_exceeded_detail=VocabularyAmountLimits.Details.EXAMPLES_AMOUNT_EXCEEDED,
            set_objs=True,
            response_serializer_class=WordSerializer,
        )

    @extend_schema(operation_id='word_example_retrieve', methods=('get',))
    @extend_schema(operation_id='word_example_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_example_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'examples/(?P<example_slug>[\w-]+)',
        serializer_class=UsageExampleInLineSerializer,
    )
    def examples_detail(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Retrieve, update, disassociate usage example for given word."""
        return self.detail_action(
            request,
            objs_related_name='examples',
            lookup_field='slug',
            lookup_query_param='example_slug',
            delete_through_manager=True,
            response_objs_name='examples',
            response_serializer_class=UsageExampleInLineSerializer,
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
    def notes(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all notes for given word."""
        return self.list_related_objs(request, objs_related_name='notes')

    @extend_schema(operation_id='word_notes_create', methods=('post',))
    @notes.mapping.post
    def notes_create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Creates new notes for given word."""
        return self.create_related_objs(
            request,
            objs_related_name='notes',
            amount_limit=VocabularyAmountLimits.MAX_NOTES_AMOUNT,
            amount_limit_exceeded_detail=VocabularyAmountLimits.MAX_NOTES_AMOUNT,
            set_objs=False,
            response_serializer_class=WordSerializer,
        )

    @extend_schema(operation_id='word_note_retrieve', methods=('get',))
    @extend_schema(operation_id='word_note_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_note_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'notes/(?P<note_slug>[\w-]+)',
        serializer_class=NoteForWordSerializer,
    )
    def notes_detail(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Retrieve, update, destroy note for given word."""
        return self.detail_action(
            request,
            objs_related_name='notes',
            lookup_field='slug',
            lookup_query_param='note_slug',
            delete_return_list=False,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_synonyms_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=SynonymForWordListSerializer,
    )
    def synonyms(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all synonyms for given word."""
        return self.list_related_objs(
            request, objs_related_name='synonym_to_words', response_objs_name='synonyms'
        )

    @extend_schema(operation_id='word_synonyms_create', methods=('post',))
    @synonyms.mapping.post
    def synonyms_create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds new synonyms for given word."""
        return self.create_related_objs(
            request,
            objs_related_name='synonym_to_words',
            response_objs_name='synonyms',
            amount_limit=VocabularyAmountLimits.MAX_SYNONYMS_AMOUNT,
            amount_limit_exceeded_detail=VocabularyAmountLimits.Details.SYNONYMS_AMOUNT_EXCEEDED,
            set_objs=False,
            response_serializer_class=WordSerializer,
        )

    @extend_schema(operation_id='word_synonym_retrieve', methods=('get',))
    @extend_schema(operation_id='word_synonym_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_synonym_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'synonyms/(?P<synonym_slug>[\w-]+)',
        serializer_class=SynonymInLineSerializer,
    )
    def synonyms_detail(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Retrieve, update, disassociate synonym for given word."""
        return self.detail_action(
            request,
            objs_related_name='synonym_to_words',
            lookup_field='from_word__slug',
            lookup_query_param='synonym_slug',
            response_objs_name='synonyms',
            response_serializer_class=SynonymForWordListSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_antonyms_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=AntonymForWordListSerializer,
    )
    def antonyms(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all antonyms for given word."""
        return self.list_related_objs(
            request, objs_related_name='antonym_to_words', response_objs_name='antonyms'
        )

    @extend_schema(operation_id='word_antonyms_create', methods=('post',))
    @antonyms.mapping.post
    def antonyms_create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds new antonyms for given word."""
        return self.create_related_objs(
            request,
            objs_related_name='antonym_to_words',
            response_objs_name='antonyms',
            amount_limit=VocabularyAmountLimits.MAX_ANTONYMS_AMOUNT,
            amount_limit_exceeded_detail=VocabularyAmountLimits.Details.ANTONYMS_AMOUNT_EXCEEDED,
            set_objs=False,
            response_serializer_class=WordSerializer,
        )

    @extend_schema(operation_id='word_antonym_retrieve', methods=('get',))
    @extend_schema(operation_id='word_antonym_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_antonym_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'antonyms/(?P<antonym_slug>[\w-]+)',
        serializer_class=AntonymInLineSerializer,
    )
    def antonyms_detail(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Retrieve, update, disassociate antonym for given word."""
        return self.detail_action(
            request,
            objs_related_name='antonym_to_words',
            lookup_field='from_word__slug',
            lookup_query_param='antonym_slug',
            response_objs_name='antonyms',
            response_serializer_class=AntonymForWordListSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_forms_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=FormForWordListSerializer,
    )
    def forms(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all forms for given word."""
        return self.list_related_objs(
            request, objs_related_name='form_to_words', response_objs_name='forms'
        )

    @extend_schema(operation_id='word_forms_create', methods=('post',))
    @forms.mapping.post
    def forms_create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds new forms for given word."""
        return self.create_related_objs(
            request,
            objs_related_name='form_to_words',
            response_objs_name='forms',
            amount_limit=VocabularyAmountLimits.MAX_FORMS_AMOUNT,
            amount_limit_exceeded_detail=VocabularyAmountLimits.Details.FORMS_AMOUNT_EXCEEDED,
            set_objs=False,
            response_serializer_class=WordSerializer,
        )

    @extend_schema(operation_id='word_form_retrieve', methods=('get',))
    @extend_schema(operation_id='word_form_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_form_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'forms/(?P<form_slug>[\w-]+)',
        serializer_class=FormInLineSerializer,
    )
    def form_detail(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Retrieve, update, disassociate form for given word."""
        return self.detail_action(
            request,
            objs_related_name='form_to_words',
            lookup_field='from_word__slug',
            lookup_query_param='form_slug',
            response_objs_name='forms',
            response_serializer_class=FormForWordListSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_similars_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=SimilarForWordListSerializer,
    )
    def similars(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all similar words for given word."""
        return self.list_related_objs(
            request, objs_related_name='similar_to_words', response_objs_name='similars'
        )

    @extend_schema(operation_id='word_similars_create', methods=('post',))
    @similars.mapping.post
    def similars_create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds new similar words for given word."""
        return self.create_related_objs(
            request,
            objs_related_name='similar_to_words',
            response_objs_name='similars',
            amount_limit=VocabularyAmountLimits.MAX_SIMILARS_AMOUNT,
            amount_limit_exceeded_detail=VocabularyAmountLimits.Details.SIMILARS_AMOUNT_EXCEEDED,
            set_objs=False,
            response_serializer_class=WordSerializer,
        )

    @extend_schema(operation_id='word_similar_retrieve', methods=('get',))
    @extend_schema(operation_id='word_similar_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_similar_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'similars/(?P<similar_slug>[\w-]+)',
        serializer_class=SimilarInLineSerializer,
    )
    def similar_detail(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Retrieve, update, disassociate similar word for given word."""
        return self.detail_action(
            request,
            objs_related_name='similar_to_words',
            lookup_field='from_word__slug',
            lookup_query_param='similar_slug',
            response_objs_name='similars',
            response_serializer_class=SimilarForWordListSerializer,
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
    def associations(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all associations of any type for given word."""
        instance = self.get_object()
        logger.debug(f'Word instance: {instance}')

        images = ImageInLineSerializer(
            instance.images_associations.all(),
            many=True,
            context={'request': request},
        )
        logger.debug(f'Word image-associations: {images.data}')

        quotes = QuoteInLineSerializer(
            instance.quotes_associations.all(),
            many=True,
            context={'request': request},
        )
        logger.debug(f'Word quote-associations: {images.data}')

        result_list = sorted(
            chain(quotes.data, images.data),
            key=lambda d: d.get('created'),
            reverse=True,
        )
        logger.debug(f'Result list: {images.data}')

        return Response(
            {
                'count': len(result_list),
                'associations': result_list,
            }
        )

    @extend_schema(operation_id='word_associations_create', methods=('post',))
    @associations.mapping.post
    @transaction.atomic
    def associations_create(
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        """Adds passed associations to given word."""
        instance = self.get_object()
        logger.debug(f'Word instance: {instance}')

        serializer = self.get_serializer(data=request.data)
        logger.debug(f'Serializer used: {type(serializer)}')

        logger.debug(f'Validating data: {request.data}')
        serializer.is_valid(raise_exception=True)

        logger.debug('Performing save')
        _data = serializer.save()

        _quotes, _images = _data.get('quotes', []), _data.get('images', [])

        logger.debug('Checking amount limits')
        try:
            check_amount_limit(
                current_amount=instance.images_associations.count(),
                new_objects_amount=len(_images),
                amount_limit=VocabularyAmountLimits.MAX_IMAGES_AMOUNT,
                detail=VocabularyAmountLimits.Details.IMAGES_AMOUNT_EXCEEDED,
            )
            check_amount_limit(
                current_amount=instance.quotes_associations.count(),
                new_objects_amount=len(_quotes),
                amount_limit=VocabularyAmountLimits.MAX_QUOTES_AMOUNT,
                detail=VocabularyAmountLimits.Details.QUOTES_AMOUNT_EXCEEDED,
            )
        except AmountLimitExceeded as exception:
            return exception.get_detail_response(request)

        logger.debug('Associate objects with instance')
        instance.quotes_associations.add(*_quotes)
        instance.images_associations.add(*_images)

        return Response(
            WordSerializer(instance, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(operation_id='word_images_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=ImageInLineSerializer,
    )
    def images(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all image associations for given word."""
        return self.list_related_objs(
            request,
            objs_related_name='images_associations',
            response_objs_name='images',
        )

    @extend_schema(operation_id='word_image_retrieve', methods=('get',))
    @extend_schema(operation_id='word_image_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_image_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'images/(?P<image_id>[\w\d-]+)',
        serializer_class=ImageInLineSerializer,
    )
    def images_detail(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Retrieve, update, disassociate image-association for given word."""
        return self.detail_action(
            request,
            objs_related_name='images_associations',
            lookup_field='id',
            lookup_query_param='image_id',
            delete_through_manager=True,
            response_serializer_class=ImageInLineSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='word_quotes_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=QuoteInLineSerializer,
    )
    def quotes(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all quote associations for given word."""
        return self.list_related_objs(
            request,
            objs_related_name='quotes_associations',
            response_objs_name='quotes',
        )

    @extend_schema(operation_id='word_quote_retrieve', methods=('get',))
    @extend_schema(operation_id='word_quote_partial_update', methods=('patch',))
    @extend_schema(operation_id='word_quote_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'quotes/(?P<quote_id>[\w\d-]+)',
        serializer_class=QuoteInLineSerializer,
    )
    def quotes_detail(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Retrieve, update, disassociate quote-association for given word."""
        return self.detail_action(
            request,
            objs_related_name='quotes_associations',
            lookup_field='id',
            lookup_query_param='quote_id',
            delete_through_manager=True,
            response_serializer_class=QuoteInLineSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='words_favorites_list', methods=('get',))
    @action(detail=False, methods=('get',), permission_classes=(IsAuthenticated,))
    def favorites(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all user's favorites words."""
        return self.list(request)

    @extend_schema(operation_id='word_favorite_create', methods=('post',))
    @action(detail=True, methods=('post',), permission_classes=(IsAuthenticated,))
    def favorite(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds given word to users's favorites."""
        return self._add_to_favorite_action(
            request,
            related_model=FavoriteWord,
            related_model_obj_field='word',
            already_exist_msg='Это слово уже находится в вашем избранном.',
        )

    @extend_schema(operation_id='word_favorite_destroy', methods=('delete',))
    @favorite.mapping.delete
    def remove_from_favorite(
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        """Removes given word from users's favorites."""
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
    def images_upload(
        self, request: HttpRequest, format: str | None = None, *args, **kwargs
    ) -> HttpResponse:
        """Uploads passed images through MultiPartParser or base64 field."""
        serializer = self.get_serializer(data=request.data)
        logger.debug(f'Serializer used: {type(serializer)}')

        logger.debug('Validating data')
        serializer.is_valid(raise_exception=True)

        logger.debug('Performing save')
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


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
    """Words translations CRUD."""

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

    def get_queryset(self) -> QuerySet[WordTranslation]:
        """Returns list of all user's words translations."""
        user = self.request.user
        if user.is_authenticated:
            return user.wordtranslations.all()
        return WordTranslation.objects.none()

    def get_serializer_class(self) -> Serializer:
        match self.action:
            case 'list' | 'destroy':
                return WordTranslationListSerializer
            case 'create':
                return WordTranslationCreateSerializer
            case _:
                return super().get_serializer_class()

    def create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns created translation data and list of its related words."""
        return self.create_return_with_words(
            request, default_order=['-wordtranslations__created'], *args, **kwargs
        )

    def retrieve(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns given translation data and list of its related words."""
        return self.retrieve_with_words(
            request, default_order=['-wordtranslations__created'], *args, **kwargs
        )

    def partial_update(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns updated translation data and list of its related words."""
        return self.partial_update_return_with_words(
            request, default_order=['-wordtranslations__created'], *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_translation', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=WordTranslationSerializer,
    )
    def add_words(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Associate passed words with given translation."""
        return self.add_words_return_retrieve_with_words(
            request, default_order=['-wordtranslations__created'], *args, **kwargs
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
    """Words usage examples CRUD."""

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

    def get_queryset(self) -> QuerySet[UsageExample]:
        """Returns list of all user's usage examples."""
        user = self.request.user
        if user.is_authenticated:
            return user.usageexamples.all()
        return UsageExample.objects.none()

    def get_serializer_class(self) -> Serializer:
        match self.action:
            case 'list' | 'destroy':
                return UsageExampleListSerializer
            case 'create':
                return UsageExampleCreateSerializer
            case _:
                return super().get_serializer_class()

    def create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns created usage example data and list of its related words."""
        return self.create_return_with_words(
            request, default_order=['-wordusageexamples__created'], *args, **kwargs
        )

    def retrieve(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns given usage example data and list of its related words."""
        return self.retrieve_with_words(
            request, default_order=['-wordusageexamples__created'], *args, **kwargs
        )

    def partial_update(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns updated usage example data and list of its related words."""
        return self.partial_update_return_with_words(
            request, default_order=['-wordusageexamples__created'], *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_example', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=UsageExampleSerializer,
    )
    def add_words(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Associate passed words with given usage example."""
        return self.add_words_return_retrieve_with_words(
            request, default_order=['-wordusageexamples__created'], *args, **kwargs
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
    """Words definitions CRUD."""

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

    def get_queryset(self) -> QuerySet[Definition]:
        """Returns list of all user's definitions."""
        user = self.request.user
        if user.is_authenticated:
            return user.definitions.all()
        return Definition.objects.none()

    def get_serializer_class(self) -> Serializer:
        match self.action:
            case 'list' | 'destroy':
                return DefinitionListSerializer
            case 'create':
                return DefinitionCreateSerializer
            case _:
                return super().get_serializer_class()

    def create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns created definition data and list of its related words."""
        return self.create_return_with_words(
            request, default_order=['-worddefinitions__created'], *args, **kwargs
        )

    def retrieve(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns given definition data and list of its related words."""
        return self.retrieve_with_words(
            request, default_order=['-worddefinitions__created'], *args, **kwargs
        )

    def partial_update(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns updated definition data and list of its related words."""
        return self.partial_update_return_with_words(
            request, default_order=['-worddefinitions__created'], *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_definition', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=DefinitionSerializer,
    )
    def add_words(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Associate passed words with given definition."""
        return self.add_words_return_retrieve_with_words(
            request, default_order=['-worddefinitions__created'], *args, **kwargs
        )


@extend_schema(tags=['associations'])
@extend_schema_view(
    list=extend_schema(operation_id='associations_list'),
)
class AssociationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Words associations CRUD."""

    http_method_names = ('get',)
    queryset = ImageAssociation.objects.none()
    serializer_class = AllUserAssociationsSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination

    def list(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns list of all user's associations of any type."""
        serializer = self.get_serializer(request.user, many=False)
        logger.debug(f'Serializer used for list user associations: {type(serializer)}')
        return Response(serializer.data)


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
    """Words image-associations CRUD."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'id'
    queryset = ImageAssociation.objects.none()
    serializer_class = ImageInLineSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering = ('-created',)
    ordering_fields = ('created', 'words_count')
    search_fields = ('words__text', 'words__translations__text')

    def get_queryset(self) -> QuerySet[ImageAssociation]:
        """Returns list of all user's image-associations."""
        user = self.request.user
        if user.is_authenticated:
            return user.imageassociations.all()
        return ImageAssociation.objects.none()

    def get_serializer_class(self) -> Serializer:
        match self.action:
            case 'list' | 'destroy':
                return ImageListSerializer
            case _:
                return super().get_serializer_class()

    def retrieve(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns given image-association data and list of its related words."""
        return self.retrieve_with_words(
            request, default_order=['-wordimageassociations__created'], *args, **kwargs
        )

    def partial_update(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns updated image-association data and list of its related words."""
        return self.partial_update_return_with_words(
            request, default_order=['-wordimageassociations__created'], *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_image', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=ImageInLineSerializer,
    )
    def add_words(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Associate passed words with given image-association."""
        return self.add_words_return_retrieve_with_words(
            request, default_order=['-wordimageassociations__created'], *args, **kwargs
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
    """Words quote-associtaions CRUD."""

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

    def get_queryset(self) -> QuerySet[QuoteAssociation]:
        """Returns list of all user's quote-associations."""
        user = self.request.user
        if user.is_authenticated:
            return user.quoteassociations.all()
        return QuoteAssociation.objects.none()

    def retrieve(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns given quote-association data and list of its related words."""
        return self.retrieve_with_words(
            request, default_order=['-wordquoteassociations__created'], *args, **kwargs
        )

    def partial_update(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns updated quote-association data and list of its related words."""
        return self.partial_update_return_with_words(
            request, default_order=['-wordquoteassociations__created'], *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_quote', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=QuoteInLineSerializer,
    )
    def add_words(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Associate passed words with given quote-association."""
        return self.add_words_return_retrieve_with_words(
            request, default_order=['-wordquoteassociations__created'], *args, **kwargs
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
    """Retrieve, update, destroy actions for words synonyms."""

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

    def get_queryset(self) -> QuerySet[Word]:
        """Returns all words with synonyms from user's vocabulary."""
        user = self.request.user
        if user.is_authenticated:
            return user.words.filter(synonyms__isnull=False).distinct()
        return Word.objects.none()

    def get_serializer_class(self) -> Serializer:
        match self.action:
            case 'partial_update':
                return WordSerializer
            case _:
                return super().get_serializer_class()

    def retrieve(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns given word data and list of its synonyms."""
        return self.retrieve_with_words(
            request,
            default_order=['-synonym_to_words__created'],
            words_related_name='synonyms',
            *args,
            **kwargs,
        )

    def partial_update(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns updated word data and list of its synonyms."""
        return self.partial_update_return_with_words(
            request,
            default_order=['-synonym_to_words__created'],
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
    def add_words(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds passed words to given word synonyms."""
        return self.add_words_return_retrieve_with_words(
            request,
            default_order=['-synonym_to_words__created'],
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
    """Retrieve, update, destroy actions for words antonyms."""

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

    def get_queryset(self) -> QuerySet[Word]:
        """Returns all words with antonyms from user's vocabulary."""
        user = self.request.user
        if user.is_authenticated:
            return user.words.filter(antonyms__isnull=False).distinct()
        return Word.objects.none()

    def get_serializer_class(self) -> Serializer:
        match self.action:
            case 'partial_update':
                return WordSerializer
            case _:
                return super().get_serializer_class()

    def retrieve(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns given word data and list of its antonyms."""
        return self.retrieve_with_words(
            request,
            default_order=['-antonym_to_words__created'],
            words_related_name='antonyms',
            *args,
            **kwargs,
        )

    def partial_update(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns updated word data and list of its antonyms."""
        return self.partial_update_return_with_words(
            request,
            default_order=['-antonym_to_words__created'],
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
    def add_words(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds passed words to given word antonyms."""
        return self.add_words_return_retrieve_with_words(
            request,
            default_order=['-antonym_to_words__created'],
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
    """Retrieve, update, destroy actions for similar words."""

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

    def get_queryset(self) -> QuerySet[Word]:
        """Returns all words with similar words from user's vocabulary."""
        user = self.request.user
        if user.is_authenticated:
            return user.words.filter(similars__isnull=False).distinct()
        return Word.objects.none()

    def get_serializer_class(self) -> Serializer:
        match self.action:
            case 'partial_update':
                return WordSerializer
            case _:
                return super().get_serializer_class()

    def retrieve(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns given word data and list of its similar words."""
        return self.retrieve_with_words(
            request,
            default_order=['-similar_to_words__created'],
            words_related_name='similars',
            *args,
            **kwargs,
        )

    def partial_update(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns updated word data and list of its similar words."""
        return self.partial_update_return_with_words(
            request,
            default_order=['-similar_to_words__created'],
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
    def add_words(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds passed words to given word similar words."""
        return self.add_words_return_retrieve_with_words(
            request,
            default_order=['-similar_to_words__created'],
            words_related_name='similars',
            *args,
            **kwargs,
        )


@extend_schema(tags=['tags'])
@extend_schema_view(list=extend_schema(operation_id='user_tags_list'))
class TagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """List all user's tags."""

    queryset = Tag.objects.none()
    serializer_class = TagListSerializer
    http_method_names = ('get',)
    pagination_class = None
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering = ('-words_count', '-created')

    def get_queryset(self) -> QuerySet[Tag]:
        # Annotate tags with words amount to use in sorting
        user = self.request.user
        if user.is_authenticated:
            return user.tags.annotate(words_count=Count('words', distinct=True))
        return Tag.objects.none()


@extend_schema(tags=['types'])
@extend_schema_view(list=extend_schema(operation_id='types_list'))
class TypeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """List all possible types of words and phrases."""

    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    lookup_field = 'slug'
    http_method_names = ('get',)
    pagination_class = None
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering = ('-words_count',)

    def get_queryset(self) -> QuerySet[Type]:
        # Annotate with words amount to use in sorting
        return Type.objects.annotate(words_count=Count('words', distinct=True))


@extend_schema(tags=['forms groups'])
@extend_schema_view(
    list=extend_schema(operation_id='formsgroups_list'),
)
class FormsGroupsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """List all user's form groups."""

    queryset = FormsGroup.objects.none()
    serializer_class = FormsGroupListSerializer
    lookup_field = 'slug'
    http_method_names = ('get',)
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)

    def get_queryset(self) -> QuerySet[FormsGroup]:
        """Returns all user's and admin user form groups."""
        user = self.request.user
        admin_user = get_admin_user(User)
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
    """Words collections CRUD."""

    queryset = Collection.objects.none()
    serializer_class = CollectionSerializer
    lookup_field = 'slug'
    http_method_names = ('get', 'post', 'patch', 'delete')
    permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)
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

    def get_queryset(self) -> QuerySet[Collection]:
        """Returns all user's collections or favorites only."""
        user = self.request.user
        if user.is_authenticated:
            match self.action:
                case 'favorites':
                    return Collection.objects.filter(favorite_for__user=user).order_by(
                        '-favorite_for__created'
                    )
                case _:
                    # Annotate with words amount to use in filters, sorting
                    return user.collections.annotate(
                        words_count=Count('words', distinct=True)
                    )
        return Collection.objects.none()

    def get_serializer_class(self) -> Serializer:
        match self.action:
            case 'list' | 'favorites' | 'destroy':
                return CollectionShortSerializer
            case _:
                return super().get_serializer_class()

    def create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns created collection data and list of all words in it."""
        return self.create_return_with_words(
            request, default_order=['-wordsincollections__created'], *args, **kwargs
        )

    def retrieve(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns given collection data and list of all words in it."""
        return self.retrieve_with_words(
            request, default_order=['-wordsincollections__created'], *args, **kwargs
        )

    def partial_update(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns updated collection data and list of all words in it."""
        return self.partial_update_return_with_words(
            request, default_order=['-wordsincollections__created'], *args, **kwargs
        )

    @extend_schema(operation_id='words_add_to_collection', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='add-words',
        serializer_class=CollectionSerializer,
    )
    def add_words(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds passed words to given collection."""
        return self.add_words_return_retrieve_with_words(
            request, default_order=['-wordsincollections__created'], *args, **kwargs
        )

    def retrieve_words_objs(
        self,
        request: HttpRequest,
        objs_response_name: str,
        objs_model: Model,
        objs_viewset: viewsets.GenericViewSet,
        objs_list_serializer: Serializer,
        *args,
        **kwargs,
    ) -> HttpResponse:
        """
        Common method to list some related objects of all words in given collection.
        """
        queryset = self.get_queryset()
        collection = get_object_or_404(
            queryset, **{self.lookup_field: self.kwargs[self.lookup_field]}
        )
        logger.debug(f'Collection instance: {collection}')

        collection_data = self.get_serializer(collection).data

        _objs = (
            objs_model.objects.filter(words__in=collection.words.all())
            .distinct()
            .annotate(words_count=Count('words'))
        )
        logger.debug(f'Obtained objects: {_objs}')

        objs_data = self.get_filtered_paginated_objs(
            request, _objs, objs_viewset, objs_list_serializer
        )

        return Response(
            {
                **collection_data,
                objs_response_name: objs_data,
            }
        )

    @extend_schema(operation_id='collection_images_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        serializer_class=CollectionSerializer,
    )
    def images(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Return list of all images of words in given collections."""
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
    def translations(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Return list of all translations of words in given collections."""
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
    def definitions(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Return list of all definitions of words in given collections."""
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
    def examples(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Return list of all usage examples of words in given collections."""
        return self.retrieve_words_objs(
            request,
            'examples',
            UsageExample,
            UsageExampleViewSet,
            UsageExampleListSerializer,
        )

    @extend_schema(operation_id='collections_favorites_list', methods=('get',))
    @action(detail=False, methods=('get',), permission_classes=(IsAuthenticated,))
    def favorites(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Return list of all user's favorite collections."""
        return self.list(request)

    @extend_schema(operation_id='collection_favorite_create', methods=('post',))
    @action(detail=True, methods=('post',), permission_classes=(IsAuthenticated,))
    def favorite(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """ADds given collection to user's favorites."""
        return self._add_to_favorite_action(
            request,
            related_model=FavoriteCollection,
            related_model_obj_field='collection',
            already_exist_msg='Эта коллекция уже находится в вашем избранном.',
        )

    @extend_schema(operation_id='collection_favorite_destroy', methods=('delete',))
    @favorite.mapping.delete
    def remove_from_favorite(
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        """Removes given collection from user's favorites."""
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
    def add_words_to_collections(
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        """Adds given words to given collections."""
        serializer = MultipleWordsSerializer(
            data=request.data, many=False, context={'request': request}
        )
        logger.debug(f'Serializer used: {type(serializer)}')

        logger.debug(f'Validating data: {request.data}')
        serializer.is_valid(raise_exception=True)

        try:
            logger.debug('Performing create')
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
            logger.error(f'ObjectAlreadyExist exception occured: {exception}')
            return exception.get_detail_response(request)


@extend_schema(tags=['languages'])
@extend_schema_view(
    list=extend_schema(operation_id='learning_languages_list'),
    create=extend_schema(operation_id='learning_language_create'),
    retrieve=extend_schema(operation_id='learning_language_retrieve'),
    destroy=extend_schema(operation_id='learning_language_destroy'),
)
class LanguageViewSet(ActionsWithRelatedObjectsMixin, viewsets.ModelViewSet):
    """User's learning, native languages CRUD."""

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

    def get_queryset(self) -> QuerySet[Language]:
        user = self.request.user
        match self.action:
            case 'native' | 'add_native_languages':
                if user.is_authenticated:
                    return user.native_languages_detail.annotate(
                        words_count=Count(
                            'user__wordtranslations',
                            filter=Q(user__wordtranslations__language=F('language')),
                        )
                    )
                return Language.objects.none()
            case 'all':
                return Language.objects.annotate(words_count=Count('words'))
            case 'learning_available':
                return (
                    Language.objects.filter(learning_available=True)
                    .exclude(learning_by=self.request.user)
                    .annotate(words_count=Count('words'))
                )
            case 'interface':
                return Language.objects.filter(interface_available=True).annotate(
                    words_count=Count('words')
                )
            case _:
                if user.is_authenticated:
                    return user.learning_languages_detail.annotate(
                        words_count=Count(
                            'user__words', filter=Q(user__words__language=F('language'))
                        )
                    )
                return Language.objects.none()

    def get_serializer_class(self) -> Serializer:
        match self.action:
            case 'list' | 'create' | 'destroy':
                # Check if `no_words_param` passed to use serializer without
                # languages last words
                no_words_param = self.request.query_params.get('no_words', None)
                logger.debug(
                    f'Languages last words representation option query parameter '
                    f'passed: {no_words_param}'
                )
                if no_words_param is not None:
                    return LearningLanguageSerailizer
                return LearningLanguageWithLastWordsSerailizer
            case _:
                return super().get_serializer_class()

    def list(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns all user's learning languages, its amount."""
        response_data = super().list(request, *args, **kwargs).data
        return Response({'count': len(response_data), 'results': response_data})

    @transaction.atomic
    def create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds passed languages to user's learning languages."""
        try:
            serializer = self.get_serializer(data=request.data, many=True)
            logger.debug(f'Serializer used: {type(serializer)}')

            logger.debug(f'Validating data: {request.data}')
            serializer.is_valid(raise_exception=True)

            # Amount limit check
            logger.debug('Checking amount limits')
            try:
                check_amount_limit(
                    current_amount=kwargs.get(
                        'current_amount', request.user.learning_languages.count()
                    ),
                    new_objects_amount=len(serializer.validated_data),
                    amount_limit=kwargs.get(
                        'amount_limit', UsersAmountLimits.MAX_LEARNING_LANGUAGES_AMOUNT
                    ),
                    detail=kwargs.get(
                        'amount_limit_exceeded_detail',
                        UsersAmountLimits.Details.LEARNING_LANGUAGES_AMOUNT_EXCEEDED,
                    ),
                )
            except AmountLimitExceeded as exception:
                return exception.get_detail_response(request)

            logger.debug('Performing create')
            self.perform_create(serializer)

            headers = self.get_success_headers(serializer.data)
            list_response_data = self.list(request).data
            return Response(
                list_response_data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

        except ObjectAlreadyExist as exception:
            return exception.get_detail_response(
                request,
                existing_obj_representation=self.existing_user_language_represent,
            )

    def retrieve(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns user's learning language details."""
        instance = kwargs.get('instance', self.get_object())
        logger.debug(f'Obtained instance: {instance}')

        serializer_class = kwargs.get('serializer_class', None)
        instance_data = (
            serializer_class(instance, many=False, context={'request': request}).data
            if serializer_class
            else self.get_serializer(instance).data
        )

        _words = instance.user.words.filter(language=instance.language).annotate(
            translations_count=Count('translations', distinct=True),
            examples_count=Count('examples', distinct=True),
            collections_count=Count('collections', distinct=True),
        )
        logger.debug(f'Obtained words: {_words}')

        words_serializer = get_words_view(request)
        logger.debug(f'Serializer used for words: {type(words_serializer)}')

        words_data = self.get_filtered_paginated_objs(
            request, _words, WordViewSet, words_serializer
        )

        return Response(
            {
                **instance_data,
                'words': words_data,
            }
        )

    def destroy(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Removes language from user's learning languages."""
        instance = self.get_object()
        logger.debug(f'Obtained instance: {instance}')

        if instance.user.words.filter(language=instance.language).exists():
            logger.debug('Deletion is prohibited')
            return Response(
                {
                    'detail': _(
                        'You cannot remove a language from learning languages if there are words in that language in your vocabulary.'
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        logger.debug('Performing destroy')
        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(operation_id='language_collections_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        permission_classes=(IsAuthenticated,),
        serializer_class=LearningLanguageSerailizer,
    )
    def collections(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns all user's collections that have words with given language."""
        instance = self.get_object()
        logger.debug(f'Obtained instance: {instance}')

        instance_data = self.get_serializer(instance).data

        _collections = instance.user.collections.filter(
            words__language=instance.language
        )
        logger.debug(f'Obtained collections: {_collections}')

        collections_data = self.get_filtered_paginated_objs(
            request, _collections, CollectionViewSet, CollectionShortSerializer
        )

        return Response(
            {
                **instance_data,
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
    def native(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns all user's native languages."""
        return self.list(request)

    @extend_schema(operation_id='native_language_create', methods=('post',))
    @native.mapping.post
    def add_native_languages(
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        """Adds passed languages to user's native languages."""
        return self.create(
            request,
            integrityerror_detail='Этот язык уже добавлен в родные.',
            amount_limit=UsersAmountLimits.MAX_NATIVE_LANGUAGES_AMOUNT,
            amount_limit_exceeded_detail=UsersAmountLimits.Details.NATIVE_LANGUAGES_AMOUNT_EXCEEDED,
            current_amount=request.user.native_languages.count(),
        )

    @extend_schema(operation_id='all_languages_list', methods=('get',))
    @action(
        methods=('get',),
        detail=False,
        serializer_class=LanguageSerializer,
        permission_classes=(AllowAny,),
        pagination_class=LimitPagination,
    )
    def all(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns all languages."""
        return super().list(request)

    @extend_schema(
        operation_id='languages_available_for_learning_list', methods=('get',)
    )
    @action(
        methods=('get',),
        detail=False,
        url_path='learning-available',
        serializer_class=LanguageSerializer,
        permission_classes=(AllowAny,),
    )
    def learning_available(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns available for learning languages."""
        return self.list(request)

    @extend_schema(operation_id='interface_switch_languages_list', methods=('get',))
    @action(
        methods=('get',),
        detail=False,
        serializer_class=LanguageSerializer,
        permission_classes=(AllowAny,),
    )
    def interface(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns all available for interface translation languages."""
        return self.list(request)

    @extend_schema(operation_id='language_cover_choices_retrieve', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        url_path='cover-choices',
        serializer_class=LanguageImageSerailizer,
        permission_classes=(IsAuthenticated,),
    )
    def cover_choices(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Returns all available images to be set as cover for given learning language.
        """
        learning_language = self.get_object()
        logger.debug(f'Obtained learning language: {learning_language}')

        serializer = self.get_serializer(
            learning_language.language.images.all(),
            many=True,
        )
        logger.debug(f'Serializer used for images: {type(serializer)}')

        return Response(serializer.data)

    @extend_schema(operation_id='language_cover_set', methods=('post',))
    @action(
        methods=('post',),
        detail=True,
        url_path='set-cover',
        serializer_class=CoverSetSerailizer,
        permission_classes=(IsAuthenticated,),
    )
    def set_language_cover(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Updates user learning language cover image."""
        serializer = self.get_serializer(data=request.data)
        logger.debug(f'Serializer used for instance: {type(serializer)}')

        logger.debug('Validating data')
        serializer.is_valid(raise_exception=True)

        language_image = serializer.validated_data.get('images', None)
        logger.debug(f'Obtained language image id: {language_image}')

        learning_language = self.get_object()
        logger.debug(f'Obtained learning language: {learning_language}')

        logger.debug('Updating learning_language cover')
        learning_language.cover = language_image.image

        logger.debug('Performing save')
        learning_language.save()

        return self.retrieve(
            request,
            instance=learning_language,
            serializer_class=LearningLanguageSerailizer,
        )

    @staticmethod
    def existing_user_language_represent(
        user_language: UserLearningLanguage | UserNativeLanguage
    ):
        return user_language.language.name


@extend_schema(tags=['main_page'])
@extend_schema_view(
    list=extend_schema(operation_id='main_page_retrieve'),
)
class MainPageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Retrieve main page data."""

    http_method_names = ('get',)
    lookup_field = 'slug'
    queryset = User.objects.none()
    serializer_class = MainPageSerailizer
    permission_classes = (IsAuthenticated,)
    pagination_class = None

    def list(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        serializer = self.get_serializer(request.user, many=False)
        logger.debug(f'Serializer used for list main page: {type(serializer)}')
        return Response(serializer.data)
