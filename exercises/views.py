"""Exercises views."""

import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from core.pagination import LimitPagination
from core.mixins import FavoriteMixin
from core.utils import get_admin_user
from core.exceptions import AmountLimitExceeded, AmountLimits
from vocabulary.views import ActionsWithRelatedWordsMixin, CollectionViewSet
from vocabulary.serializers import CollectionShortSerializer

from .serializers import (
    ExerciseListSerializer,
    ExerciseProfileSerializer,
    SetListSerializer,
    SetSerializer,
    LastApproachProfileSerializer,
    TranslatorCollectionsSerializer,
    TranslatorUserDefaultSettingsSerializer,
)
from .models import (
    Exercise,
    FavoriteExercise,
    TranslatorUserDefaultSettings,
)
from .constants import exercises_lookups

logger = logging.getLogger(__name__)

User = get_user_model()


@extend_schema(tags=['exercises'])
@extend_schema_view(
    list=extend_schema(operation_id='exercises_list'),
    retrieve=extend_schema(operation_id='exercise_retrieve'),
)
class ExerciseViewSet(
    ActionsWithRelatedWordsMixin,
    FavoriteMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Retrieve, list exercises."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'slug'
    queryset = Exercise.objects.all()
    serializer_class = ExerciseListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    ordering = ('available', '-created')

    def get_queryset(self) -> QuerySet[Exercise]:
        """
        Returns all exercises or favorites only or available only.
        """
        match self.action:
            case 'favorites':
                return Exercise.objects.filter(
                    favorite_for__user=self.request.user
                ).order_by('-favorite_for__created')
            case 'list':
                return Exercise.objects.filter(available=True)
            case _:
                return super().get_queryset()

    def get_serializer_class(self, *args, **kwargs) -> Serializer:
        match self.action:
            case 'retrieve':
                return ExerciseProfileSerializer
            case 'word_sets_create':
                return SetSerializer
            case _:
                return super().get_serializer_class(*args, **kwargs)

    def list(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns separate lists of available, unavailable exercises."""
        logger.debug('Obtaining available exercises data')
        response = super().list(request, *args, **kwargs)

        logger.debug('Obtaining unavailable exercises data')
        response.data['unavailable'] = self.get_serializer(
            Exercise.objects.filter(available=False), many=True
        ).data

        return response

    @extend_schema(operation_id='exercises_list_for_anonymous', methods=('get',))
    @action(
        methods=('get',),
        detail=False,
        permission_classes=(AllowAny,),
        serializer_class=ExerciseListSerializer,
    )
    def anonymous(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns exercises list for anonymous users."""
        return self.list(request)

    @extend_schema(operation_id='exercise_words_sets_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        url_path='word-sets',
        serializer_class=SetListSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def word_sets(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns all words sets list for given exercise."""
        return self.list_related_objs(
            request,
            objs_related_name='word_sets',
            search_fields=['name', 'words__text'],
        )

    @extend_schema(operation_id='exercise_words_sets_create', methods=('post',))
    @word_sets.mapping.post
    def word_sets_create(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Creates new words sets, returns words sets updated list."""
        return self.create_related_objs(
            request,
            objs_related_name='word_sets',
            amount_limit=AmountLimits.Exercises.MAX_WORD_SETS_AMOUNT_LIMIT,
            amount_limit_exceeded_detail=AmountLimits.Exercises.Details.WORD_SETS_AMOUNT_EXCEEDED,
            set_objs=False,
            return_objs_list=True,
        )

    @extend_schema(operation_id='exercise_words_set_retrieve', methods=('get',))
    @extend_schema(operation_id='exercise_words_set_partial_update', methods=('patch',))
    @extend_schema(operation_id='exercise_words_set_destroy', methods=('delete',))
    @action(
        methods=('get', 'patch', 'delete'),
        detail=True,
        url_path=r'word-sets/(?P<word_set_slug>[\w-]+)',
        serializer_class=SetSerializer,
    )
    def word_sets_detail(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Words sets retrieve, partial_update, destroy actions."""
        return self.detail_action(
            request,
            objs_related_name='word_sets',
            lookup_field='slug',
            lookup_query_param='word_set_slug',
            list_serializer=SetListSerializer,
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='exercise_last_approach_retrieve', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        url_path='last-approach',
        serializer_class=LastApproachProfileSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def last_approach(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns user last approach details of current exercise."""
        instance: Exercise = self.get_object()
        logger.debug(f'Obtained instance: {instance}')

        try:
            serializer = self.get_serializer(
                instance.users_history.filter(user=request.user).latest()
            )
            logger.debug(f'Serializer used: {type(serializer)}')

            return Response(serializer.data)

        except ObjectDoesNotExist as exception:
            logger.error(f'ObjectDoesNotExist exception occured: {exception}')
            return Response(
                {'detail': _("You haven't done this exercise yet.")},
                status=status.HTTP_409_CONFLICT,
            )

    @extend_schema(operation_id='exercise_available_words_retrieve', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        url_path='available-words',
        serializer_class=ExerciseListSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def available_words(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Returns given exercise details and available for this exercise words list.
        """
        # Determine the available words depending on the given exercise
        match self.kwargs[self.lookup_field]:
            case exercises_lookups.TRANSLATOR_EXERCISE_SLUG:
                logger.debug(
                    'Obtaining words available for `Translator` exercise '
                    'from user vocabulary'
                )
                words = request.user.words.filter(translations__isnull=False)
            case _:
                logger.debug(
                    f'Passed {self.lookup_field} has no match with available '
                    f'exercises slugs ({self.kwargs[self.lookup_field]})'
                )
                words = request.user.words.none()

        return self.retrieve_with_words(
            request, default_order=['-created'], words=words, *args, **kwargs
        )

    @extend_schema(
        operation_id='exercise_available_collections_retrieve', methods=('get',)
    )
    @action(
        methods=('get',),
        detail=True,
        url_path='available-collections',
        serializer_class=ExerciseListSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def available_collections(
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        """
        Returns given exercise details and available for this exercise collections
        list.
        """
        instance = self.get_object()
        logger.debug(f'Obtained instance: {instance}')

        instance_data = self.get_serializer(instance).data

        # Determine the available collections depending on the given exercise
        match self.kwargs[self.lookup_field]:
            case exercises_lookups.TRANSLATOR_EXERCISE_SLUG:
                logger.debug(
                    'Obtaining collections available for `Translator` exercise '
                    'from user collections'
                )
                _collections = request.user.collections.filter(
                    words__translations__isnull=False
                ).distinct()

                collections_serializer_class = TranslatorCollectionsSerializer
            case _:
                logger.debug(
                    f'Passed {self.lookup_field} has no match with available '
                    f'exercises slugs'
                )
                _collections = request.user.collections.none()

                collections_serializer_class = CollectionShortSerializer

        collections_data = self.get_filtered_paginated_objs(
            request,
            _collections,
            CollectionViewSet,
            collections_serializer_class,
        )

        return Response(
            {
                **instance_data,
                'collections': collections_data,
            }
        )

    @extend_schema(
        operation_id='translator_default_settings_retrieve', methods=('get',)
    )
    @action(
        methods=('get',),
        detail=False,
        url_path='translator-default-settings',
        serializer_class=TranslatorUserDefaultSettingsSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def translator_default_settings(
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        """Returns user default settings for `Translator` exercise."""
        # Retrieve user settings or admin user (default) settings if not exist
        try:
            translator_settings = request.user.translator_settings
            logger.debug(f'Obtained user settings: {translator_settings}')
        except TranslatorUserDefaultSettings.DoesNotExist as exception:
            logger.debug(f'RelatedObjectDoesNotExist exception occured: {exception}')
            admin_user = get_admin_user(User)
            translator_settings = admin_user.translator_settings
            logger.debug(
                f'Obtained admin user (default) settings: {translator_settings}'
            )

        serializer = self.get_serializer(translator_settings)
        logger.debug(f'Serializer used: {type(serializer)}')

        return Response(serializer.data)

    @extend_schema(
        operation_id='translator_default_settings_partial_update', methods=('patch',)
    )
    @translator_default_settings.mapping.patch
    def update_translator_default_settings(
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        """Updates user default settings for `Translator` exercise."""
        # Update user settings or create if not exist
        try:
            instance = request.user.translator_settings
            logger.debug(f'Obtained instance: {instance}')

            serializer = self.get_serializer(instance, data=request.data, partial=True)
            logger.debug(f'Serializer used: {type(serializer)}')
        except TranslatorUserDefaultSettings.DoesNotExist as exception:
            logger.debug(f'RelatedObjectDoesNotExist exception occured: {exception}')
            instance = None

            serializer = self.get_serializer(data=request.data)
            logger.debug(f'Serializer used: {type(serializer)}')
        except AmountLimitExceeded as exception:
            logger.error(f'AmountLimitExceeded exception occured: {exception}')
            return exception.get_detail_response(request)

        logger.debug('Validating data')
        serializer.is_valid(raise_exception=True)

        logger.debug('Performing save')
        serializer.save()

        if instance and getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @extend_schema(operation_id='exercises_favorites_list')
    @action(methods=('get',), detail=False, permission_classes=(IsAuthenticated,))
    def favorites(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Returns user's favorite exercises."""
        return self.list(request)

    @extend_schema(operation_id='exercise_favorite_create')
    @action(methods=('post',), detail=True, permission_classes=(IsAuthenticated,))
    def favorite(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Adds given exercise to user's favorites."""
        return self._add_to_favorite_action(
            request,
            related_model=FavoriteExercise,
            related_model_obj_field='exercise',
            already_exist_msg='Это упражнение уже находится в вашем избранном.',
        )

    @extend_schema(operation_id='exercise_favorite_destroy')
    @favorite.mapping.delete
    def remove_from_favorite(
        self, request: HttpRequest, *args, **kwargs
    ) -> HttpResponse:
        """Removes given exercise from user's favorites."""
        return self._remove_from_favorite_action(
            request,
            related_model=FavoriteExercise,
            related_model_obj_field='exercise',
            not_found_msg='Этого упражнения нет в вашем избранном.',
        )
