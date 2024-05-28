"""Exercises views."""

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from core.pagination import LimitPagination
from core.mixins import FavoriteMixin
from vocabulary.views import ActionsWithRelatedWordsMixin, CollectionViewSet

from .serializers import (
    ExerciseListSerializer,
    ExerciseProfileSerializer,
    SetListSerializer,
    SetSerializer,
    LastApproachProfileSerializer,
    CollectionWithAvailableWordsSerializer,
    TranslatorUserDefaultSettingsSerializer,
)
from .models import (
    Exercise,
    FavoriteExercise,
    WordSet,
)
from .constants import ExercisesAmountLimits

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
    """Просмотр библиотеки упражнений."""

    http_method_names = ('get', 'post', 'patch', 'delete')
    lookup_field = 'slug'
    queryset = Exercise.objects.all()
    serializer_class = ExerciseListSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitPagination
    ordering = ('available', '-created')

    def get_queryset(self):
        match self.action:
            case 'favorites':
                return Exercise.objects.filter(
                    favorite_for__user=self.request.user
                ).order_by('-favorite_for__created')
            case 'list':
                return Exercise.objects.filter(available=True)
            case _:
                return super().get_queryset()

    def get_serializer_class(self, *args, **kwargs):
        match self.action:
            case 'retrieve':
                return ExerciseProfileSerializer
            case 'word_sets_create':
                return SetSerializer
            case _:
                return super().get_serializer_class(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        res = super().list(request, *args, **kwargs)
        res.data['others'] = self.get_serializer(
            Exercise.objects.filter(available=False), many=True
        ).data
        return res

    @extend_schema(operation_id='exercises_list_for_anonymous', methods=('get',))
    @action(
        methods=('get',),
        detail=False,
        permission_classes=(AllowAny,),
        serializer_class=ExerciseListSerializer,
    )
    def anonymous(self, request, *args, **kwargs):
        return self.list(request)

    @extend_schema(operation_id='exercise_sets_list', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        url_path='word-sets',
        serializer_class=SetListSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def word_sets(self, request, *args, **kwargs):
        """Получить все наборы слов."""
        return self.list_related_objs(
            request,
            objs_related_name='word_sets',
            search_fields=['name', 'words__text'],
        )

    @extend_schema(operation_id='exercise_sets_create', methods=('post',))
    @word_sets.mapping.post
    def word_sets_create(self, request, *args, **kwargs):
        """Добавить новые наборы."""
        return self.create_related_objs(
            request,
            objs_related_name='word_sets',
            amount_limit=ExercisesAmountLimits.EXERCISE_MAX_WORD_SETS,
            related_model=WordSet,
            set_objs=False,
            return_objs_list=True,
        )

    @extend_schema(operation_id='exercise_set_retrieve', methods=('get',))
    @extend_schema(operation_id='exercise_set_partial_update', methods=('patch',))
    @action(
        methods=('get', 'patch'),
        detail=True,
        url_path=r'word-sets/(?P<word_set_slug>[\w-]+)',
        serializer_class=SetSerializer,
    )
    def word_sets_detail(self, request, *args, **kwargs):
        """Получить, редактировать или удалить набор слов."""
        return self.detail_action(
            request,
            objs_related_name='word_sets',
            lookup_field='slug',
            lookup_attr_name='word_set_slug',
            *args,
            **kwargs,
        )

    @extend_schema(operation_id='exercise_set_destroy', methods=('delete',))
    @word_sets_detail.mapping.delete
    def delete_word_set(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            _obj = instance.word_sets.get(slug=kwargs.get('word_set_slug'))
        except ObjectDoesNotExist:
            raise NotFound
        _obj.delete()
        return self.list_related_objs(
            request,
            'word_sets',
            status_code=status.HTTP_204_NO_CONTENT,
            serializer_class=SetListSerializer,
        )

    @extend_schema(operation_id='exercise_last_approach_retrieve', methods=('get',))
    @action(
        methods=('get',),
        detail=True,
        url_path='last-approach',
        serializer_class=LastApproachProfileSerializer,
        permission_classes=(IsAuthenticated,),
    )
    def last_approach(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            serializer = self.get_serializer(
                instance.users_history.filter(user=request.user).latest()
            )
            return Response(serializer.data)
        except ObjectDoesNotExist:
            return Response(
                {'detail': _("You haven't done this exercise yet")},
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
    def available_words(self, request, *args, **kwargs):
        match self.kwargs[self.lookup_field]:
            case 'translator':
                words = request.user.words.filter(translations__isnull=False)
            case _:
                words = request.user.words.none()
        return self.retrieve_with_words(
            request, default_order='-created', words=words, *args, **kwargs
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
    def available_collections(self, request, *args, **kwargs):
        instance = self.get_object()
        response_data = self.get_serializer(instance).data
        _collections = request.user.collections.filter(
            words__translations__isnull=False
        ).distinct()
        collections_data = self.get_filtered_paginated_objs(
            request,
            _collections,
            CollectionViewSet,
            CollectionWithAvailableWordsSerializer,
        )
        return Response(
            {
                **response_data,
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
    def translator_default_settings(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user.translator_settings)
        return Response(serializer.data)

    @extend_schema(
        operation_id='translator_default_settings_partial_update', methods=('patch',)
    )
    @translator_default_settings.mapping.patch
    def update_translator_default_settings(self, request, *args, **kwargs):
        instance = request.user.translator_settings
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @extend_schema(operation_id='exercises_favorites_list')
    @action(methods=('get',), detail=False, permission_classes=(IsAuthenticated,))
    def favorites(self, request):
        """Получить список избранных упражнений."""
        return self.list(request)

    @extend_schema(operation_id='exercise_favorite_create')
    @action(methods=('post',), detail=True, permission_classes=(IsAuthenticated,))
    def favorite(self, request, slug):
        """Добавить упражнение в избранное."""
        return self._add_to_favorite_action(
            request,
            related_model=FavoriteExercise,
            related_model_obj_field='exercise',
            already_exist_msg='Это упражнение уже находится в вашем избранном.',
        )

    @extend_schema(operation_id='exercise_favorite_destroy')
    @favorite.mapping.delete
    def remove_from_favorite(self, request, slug):
        """Удалить упражнение из избранного."""
        return self._remove_from_favorite_action(
            request,
            related_model=FavoriteExercise,
            related_model_obj_field='exercise',
            not_found_msg='Этого упражнения нет в вашем избранном.',
        )
