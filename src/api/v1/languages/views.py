"""Languages app views."""

import logging

from django.db import transaction
from django.db.models import Count, Case, When, Value, Q, F
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse

from rest_framework import filters, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend

from apps.languages.models import Language, UserLearningLanguage, UserNativeLanguage
from apps.core.exceptions import (
    AmountLimitExceeded,
    ObjectAlreadyExist,
    AmountLimits,
)
from utils.checkers import check_amount_limit

from .serializers import (
    LanguageSerializer,
    LearningLanguageSerailizer,
    NativeLanguageSerailizer,
    LanguageCoverImageSerailizer,
    CoverSetSerailizer,
)
from ..core.mixins import ActionsWithRelatedObjectsMixin
from ..vocabulary.serializers import (
    LearningLanguageWithLastWordsSerailizer,
    CollectionShortSerializer,
)
from ..vocabulary.views import WordViewSet, CollectionViewSet, get_word_cards_type

logger = logging.getLogger(__name__)


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
    lookup_field = 'language__name'
    queryset = UserLearningLanguage.objects.none()
    serializer_class = LearningLanguageSerailizer
    permission_classes = (IsAuthenticated,)
    pagination_class = None
    filter_backends = (
        filters.OrderingFilter,
        filters.SearchFilter,
        DjangoFilterBackend,
    )
    ordering = ('-created', 'language__name')
    ordering_fields = (
        'created',
        'language__name',
        'words_count',
    )
    search_fields = (
        'language__name',
        'language__name_local',
    )

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        match self.action:
            case 'all':
                return Language.objects.annotate(words_count=Count('words'))
            case 'learning_available':
                if user.is_anonymous:
                    # Ingore learning languages for anonymous user
                    return Language.objects.filter(learning_available=True).order_by(
                        '-sorting', 'name'
                    )
                return (
                    Language.objects.filter(learning_available=True)
                    .exclude(learning_by=self.request.user)
                    .annotate(words_count=Count('words'))
                    .order_by('-sorting', 'name')
                )
            case 'all':
                return Language.objects.annotate(words_count=Count('words'))
            case 'interface':
                try:
                    learning_list = user.learning_languages.values_list(
                        'name', flat=True
                    )
                    native_list = user.native_languages.values_list('name', flat=True)
                except AttributeError:
                    # Ingore learning and native languages for anonymous user
                    return Language.objects.filter(interface_available=True).order_by(
                        '-sorting', 'name'
                    )
                return (
                    Language.objects.filter(interface_available=True)
                    .annotate(
                        is_learning_or_native=Case(
                            When(
                                name__in=[*learning_list, *native_list],
                                then=Value(True),
                            ),
                            default=Value(False),
                        ),
                        words_count=Count('words'),
                    )
                    .order_by('-is_learning_or_native', '-sorting', 'name')
                )
            case 'native':
                if user.is_authenticated:
                    return user.native_languages_detail.annotate(
                        words_count=Count(
                            'user__wordtranslations',
                            filter=Q(user__wordtranslations__language=F('language')),
                        )
                    )
                return Language.objects.none()
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
                # Check if `no_words` query param passed to use serializer without
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
                        'amount_limit', AmountLimits.Users.MAX_LEARNING_LANGUAGES_AMOUNT
                    ),
                    detail=kwargs.get(
                        'amount_limit_exceeded_detail',
                        AmountLimits.Users.Details.LEARNING_LANGUAGES_AMOUNT_EXCEEDED,
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
                existing_obj_representation=self.existing_language_represent,
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

        words_serializer = get_word_cards_type(request)
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
        instance: UserLearningLanguage = self.get_object()
        logger.debug(f'Obtained instance: {instance}')

        # Check if `delete_words` query param passed to delete words
        # related to this language
        delete_words_param = self.request.query_params.get('delete_words', None)
        logger.debug(
            f'Removing words related to this language option query parameter '
            f'passed: {delete_words_param}'
        )
        if delete_words_param is not None:
            logger.debug('Removing related words')
            language_words: QuerySet = instance.user.words.filter(
                language=instance.language
            )
            language_words_amount = language_words.count()
            language_words.delete()

            logger.debug('Performing destroy')
            self.perform_destroy(instance)

            return Response(
                {
                    'deleted_words': language_words_amount,
                },
                status=status.HTTP_200_OK,
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
        ordering_fields=None,
        filter_backends=(
            filters.OrderingFilter,
            DjangoFilterBackend,
        ),
        search_fields=None,
    )
    def native(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns all user's native languages."""
        return self.list(request)

    @extend_schema(operation_id='all_languages_list', methods=('get',))
    @action(
        methods=('get',),
        detail=False,
        serializer_class=LanguageSerializer,
        permission_classes=(AllowAny,),
        ordering=('-sorting', 'name'),
        ordering_fields=None,
        search_fields=('name', 'name_local'),
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
        ordering=('-sorting', 'name'),
        ordering_fields=None,
        search_fields=('name', 'name_local'),
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
        ordering=None,
        ordering_fields=None,
        search_fields=('name', 'name_local'),
    )
    def interface(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns all available for interface translation languages."""
        return self.list(request)

    @extend_schema(operation_id='language_cover_choices_retrieve', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        url_path='cover-choices',
        serializer_class=LanguageCoverImageSerailizer,
        permission_classes=(IsAuthenticated,),
        filter_backends=[],
    )
    def cover_choices(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Returns all available images to be set as cover for given learning language.
        """
        learning_language: UserLearningLanguage = self.get_object()
        logger.debug(f'Obtained learning language: {learning_language}')

        serializer = self.get_serializer(
            (
                learning_language.language.images.annotate(
                    is_current_cover=Case(
                        When(id=learning_language.cover.id, then=Value(True)),
                        default=Value(False),
                    )
                ).order_by('-is_current_cover')
            ),
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

        new_cover = serializer.validated_data.get('images', None)
        logger.debug(f'Obtained language image: {new_cover}')

        learning_language: UserLearningLanguage = self.get_object()
        logger.debug(f'Obtained learning language: {learning_language}')

        logger.debug('Updating learning language cover')
        learning_language.cover = new_cover
        learning_language.save()

        return self.retrieve(
            request,
            instance=learning_language,
            serializer_class=LearningLanguageSerailizer,
        )

    @staticmethod
    def existing_language_represent(
        user_language: UserLearningLanguage | UserNativeLanguage
    ):
        return user_language.language.name
