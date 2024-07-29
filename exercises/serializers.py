"""Exercises serializers."""

from datetime import timedelta

from django.utils.translation import gettext as _
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.query import QuerySet

from rest_framework import serializers
from rest_framework.fields import Field
from drf_spectacular.utils import extend_schema_field
from drf_extra_fields.relations import PresentablePrimaryKeyRelatedField
from rest_framework.utils.serializer_helpers import ReturnDict

from core.serializers_mixins import (
    CountObjsSerializerMixin,
    FavoriteSerializerMixin,
    AlreadyExistSerializerHandler,
)
from core.serializers_fields import KwargsMethodField, ReadableHiddenField
from vocabulary.serializers import (
    WordShortCardSerializer,
    WordSuperShortSerializer,
    CollectionShortSerializer,
)
from vocabulary.models import Word, Collection

from .models import (
    Exercise,
    WordSet,
    FavoriteExercise,
    UsersExercisesHistory,
    ExerciseHistoryDetails,
    WordsUpdateHistory,
    TranslatorUserDefaultSettings,
    Hint,
)
from .constants import ExercisesAmountLimits, exercises_lookups


class CurrentExerciseDefault:
    """
    The current exercise as the default value for the field.
    Lookup field must be `slug`.
    """

    requires_context = True

    def __call__(self, serializer_field: Field) -> QuerySet[Exercise] | Exercise:
        request_word_slug = serializer_field.context['view'].kwargs.get('slug')
        try:
            return Exercise.objects.get(slug=request_word_slug)
        except KeyError:
            return Exercise.objects.none()

    def __repr__(self) -> str:
        return '%s()' % self.__class__.__name__


class ExerciseListSerializer(FavoriteSerializerMixin, serializers.ModelSerializer):
    """Serializer to list exercises."""

    new_for_user = serializers.SerializerMethodField('get_new_for_user')

    class Meta:
        model = Exercise
        favorite_model = FavoriteExercise
        favorite_model_field = 'exercise'
        fields = (
            'id',
            'slug',
            'name',
            'description',
            'icon',
            'constraint_description',
            'available',
            'favorite',
            'new_for_user',
        )
        read_only_fields = fields

    @extend_schema_field({'type': 'boolean'})
    def get_new_for_user(self, obj: Exercise) -> bool:
        """
        Returns False if user has already completed this exercise once
        (exercises is not new for that user), else True.
        Always False for anonymous users.
        """
        user = self.context.get('request').user
        return (
            user.is_authenticated and not obj.users_history.filter(user=user).exists()
        )


class SetSerializer(
    AlreadyExistSerializerHandler, CountObjsSerializerMixin, serializers.ModelSerializer
):
    """Serializer to retrieve set of words in exercise."""

    words_count = KwargsMethodField(
        'get_objs_count',
        objs_related_name='words',
    )
    words = PresentablePrimaryKeyRelatedField(
        queryset=Word.objects.all(),
        required=False,
        many=True,
        presentation_serializer=WordShortCardSerializer,
    )
    author = ReadableHiddenField(
        default=serializers.CurrentUserDefault(),
        representation_field='username',
    )
    exercise = ReadableHiddenField(
        default=CurrentExerciseDefault(), representation_field='name'
    )

    already_exist_detail = _('Same word set already exists.')

    class Meta:
        model = WordSet
        fields = (
            'id',
            'slug',
            'author',
            'exercise',
            'name',
            'words_count',
            'words',
        )
        read_only_fields = (
            'id',
            'slug',
            'words_count',
        )


class SetListSerializer(SetSerializer):
    """Serializer to list, create set of words in exercise."""

    last_3_words = serializers.SerializerMethodField('get_last_3_words')

    class Meta(SetSerializer.Meta):
        fields = (
            'id',
            'slug',
            'author',
            'name',
            'words_count',
            'last_3_words',
        )
        read_only_fields = fields

    @extend_schema_field({'type': 'string'})
    def get_last_3_words(self, obj: WordSet) -> QuerySet[Word]:
        """Returns list of 3 last added words in given set."""
        return obj.words.order_by('-last_exercise_date').values_list('text', flat=True)[
            :3
        ]


class HintSerializer(serializers.ModelSerializer):
    """Serializer to retrieve exercise hint."""

    class Meta:
        model = Hint
        fields = (
            'id',
            'name',
            'description',
            'code',
        )
        read_only_fields = fields


class ExerciseHistoryDetailsSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve history details of user passing `Translator` exercise.
    """

    task_word = WordSuperShortSerializer(
        many=False,
        read_only=True,
    )
    verdict = serializers.SerializerMethodField(
        'get_verdict_display',
    )
    hints_used = HintSerializer(
        many=True,
        read_only=True,
    )
    user_answer = serializers.SerializerMethodField(
        'get_user_answer',
    )
    correct_answer = serializers.SerializerMethodField(
        'get_correct_answer',
    )

    class Meta:
        model = ExerciseHistoryDetails
        fields = (
            'id',
            'task_word',
            'correct_answer',
            'user_answer',
            'verdict',
            'suggested_options',
            'answer_time',
            'hints_used',
            'created',
        )
        read_only_fields = fields

    @extend_schema_field({'type': 'string'})
    def get_verdict_display(self, obj: ExerciseHistoryDetails) -> str:
        """Get verdict full text for display."""
        return obj.get_verdict_display()

    @extend_schema_field({'type': 'dict'})
    def get_user_answer(self, obj: ExerciseHistoryDetails) -> dict:
        """Returns type, value of user answer."""
        if obj.text_answer:
            return {
                'type': 'text',
                'answer': obj.text_answer,
            }

        return {}

    @extend_schema_field({'type': 'dict'})
    def get_correct_answer(self, obj: ExerciseHistoryDetails) -> dict:
        """Returns type, value of correct answer."""
        match obj.approach.exercise.slug:
            case exercises_lookups.TRANSLATOR_EXERCISE_SLUG:
                correct_translations = obj.task_word.translations.values_list(
                    'text', flat=True
                )
                return {
                    'type': 'text',
                    'answer': correct_translations,
                }
            case _:
                return {}


class LastApproachShortSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve history details of last exercise approach by user.
    """

    mode = serializers.SerializerMethodField(
        'get_mode_display',
    )
    details = ExerciseHistoryDetailsSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = UsersExercisesHistory
        fields = (
            'id',
            'words_amount',
            'corrects_amount',
            'incorrects_amount',
            'set_time_limit',
            'complete_time',
            'mode',
            'details',
            'created',
        )
        read_only_fields = fields

    @extend_schema_field({'type': 'string'})
    def get_mode_display(self, obj: UsersExercisesHistory) -> str:
        """Get mode full text for display."""
        return obj.get_mode_display()


class ExerciseProfileSerializer(
    FavoriteSerializerMixin, CountObjsSerializerMixin, serializers.ModelSerializer
):
    """Serializer to retrieve exercise details."""

    word_sets = serializers.SerializerMethodField(
        'get_word_sets',
    )
    last_approach_preview = serializers.SerializerMethodField(
        'get_last_approach_preview',
    )
    hints_available = HintSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Exercise
        favorite_model = FavoriteExercise
        favorite_model_field = 'exercise'
        fields = (
            'id',
            'slug',
            'name',
            'icon',
            'constraint_description',
            'available',
            'favorite',
            'hints_available',
            'last_approach_preview',
            'word_sets',
        )
        read_only_fields = fields

    @extend_schema_field({'type': 'object'})
    def get_word_sets(self, obj: Exercise) -> dict:
        """Returns available words sets for given exercise and its amount."""
        user = self.context.get('request').user
        queryset = user.wordsets.filter(exercise=obj)
        return {
            'count': queryset.count(),
            'results': SetListSerializer(
                queryset,
                many=True,
            ).data,
        }

    @extend_schema_field(LastApproachShortSerializer(many=False))
    def get_last_approach_preview(self, obj: Exercise) -> ReturnDict | list:
        """Returns latest approach in given exercise details."""
        user = self.context.get('request').user
        try:
            return LastApproachShortSerializer(
                user.exercises_history.filter(exercise=obj).latest()
            ).data
        except ObjectDoesNotExist:
            return []


class WordUpdateSerializer(serializers.ModelSerializer):
    """Serializer to retrieve word activity status changes."""

    word = WordSuperShortSerializer(
        many=False,
        read_only=True,
    )

    class Meta:
        model = WordsUpdateHistory
        fields = (
            'id',
            'word',
            'activity_status',
            'new_activity_status',
            'created',
        )
        read_only_fields = fields


class LastApproachProfileSerializer(LastApproachShortSerializer):
    """
    Serializer to retrieve full history details of last exercise approach by user.
    """

    exercise = ExerciseListSerializer(
        many=False,
        read_only=True,
    )
    words_updates = WordUpdateSerializer(
        many=True,
        read_only=True,
    )
    status_counters = serializers.SerializerMethodField('get_status_counters')

    class Meta(LastApproachShortSerializer.Meta):
        fields = LastApproachShortSerializer.Meta.fields + (
            'exercise',
            'status_counters',
            'words_updates',
        )

    @extend_schema_field({'type': 'object'})
    def get_status_counters(self, obj: UsersExercisesHistory) -> dict:
        """Returns list of each new status words amount."""
        new_statuses = obj.words_updates.values_list('new_activity_status', flat=True)
        result = {}
        for status in new_statuses:
            if status in result:
                result[status] += 1
            else:
                result[status] = 1
        return result


class CollectionWithAvailableWordsSerializer(CollectionShortSerializer):
    """
    Common serializer to list collections with counter of available words for some
    exercise in each collection.
    """

    available_words_count = serializers.SerializerMethodField(
        'get_available_words_count'
    )

    class Meta(CollectionShortSerializer.Meta):
        fields = CollectionShortSerializer.Meta.fields + ('available_words_count',)

    @extend_schema_field({'type': 'integer'})
    def get_available_words_count(self, obj: Collection) -> int:
        """
        Redefine this to get the amount of available words for a particular exercise.
        """
        pass


class TranslatorCollectionsSerializer(CollectionWithAvailableWordsSerializer):
    """
    Serializer to list collections with counters of available words for `Translator`
    exercise in each collection.
    """

    @extend_schema_field({'type': 'integer'})
    def get_available_words_count(self, obj: Collection) -> int:
        """Count words that have at least one translation."""
        return obj.words.filter(translations__isnull=False).count()


class TranslatorUserDefaultSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve, update users default settings for `Translator` exercise.
    """

    from_language = serializers.SerializerMethodField('get_from_language_display')
    mode = serializers.SerializerMethodField('get_mode_display')
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = TranslatorUserDefaultSettings
        fields = (
            'mode',
            'set_time_limit',
            'repetitions_amount',
            'from_language',
            'user',
        )

    @extend_schema_field({'type': 'string'})
    def get_from_language_display(self, obj: TranslatorUserDefaultSettings) -> str:
        """Get `from_language` mode full text for display."""
        return obj.get_from_language_display()

    @extend_schema_field({'type': 'string'})
    def get_mode_display(self, obj: TranslatorUserDefaultSettings) -> str:
        """Get mode full text for display."""
        return obj.get_mode_display()

    def validate_set_time_limit(self, set_time_limit: timedelta) -> timedelta:
        """
        Checks that `set_time` value does not exceed the specified limits.
        """
        min_limit = ExercisesAmountLimits.TRANSLATOR_MIN_TIME_LIMIT
        max_limit = ExercisesAmountLimits.TRANSLATOR_MAX_TIME_LIMIT
        if not (min_limit <= set_time_limit <= max_limit):
            raise ValidationError(
                (f'Time limit must be in range from {min_limit} to {max_limit}.'),
                code='set_time_limit_exceeded',
            )
        return set_time_limit

    def validate_repetitions_amount(self, repetitions_amount: int) -> int:
        """
        Checks that `repetitions_amount` value does not exceed the specified limits.
        """
        min_amount = ExercisesAmountLimits.EXERCISE_MIN_REPETITIONS_AMOUNT
        max_amount = ExercisesAmountLimits.EXERCISE_MAX_REPETITIONS_AMOUNT
        if not (min_amount <= repetitions_amount <= max_amount):
            raise ValidationError(
                (
                    f'Repetitions amount must be in range from {min_amount} to {max_amount}.'
                ),
                code='repetitions_amount_exceeded',
            )
        return repetitions_amount
