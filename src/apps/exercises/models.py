"""Exercises app models."""

import uuid
import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.core.models import (
    GetObjectBySlugModelMixin,
    CreatedModel,
    ModifiedModel,
    SlugModel,
    AuthorModel,
    ActivityStatusModel,
)
from apps.core.signals import admin_created
from utils.fillers import slug_filler
from config.settings import AUTH_USER_MODEL

from .constants import ExercisesLengthLimits, MAX_TEXT_ANSWER_LENGTH

logger = logging.getLogger(__name__)


class Exercise(
    SlugModel,
    CreatedModel,
    ModifiedModel,
):
    """Exercises with words available in the app."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        _('Exercise name'),
        max_length=256,
    )
    description = models.CharField(
        _('Description'),
        max_length=4096,
    )
    constraint_description = models.CharField(
        _('Constraint description'),
        max_length=512,
        blank=True,
    )
    icon = models.ImageField(
        _('Exercise icon'),
        upload_to='exercises/icons/',
        blank=True,
        null=True,
    )
    available = models.BooleanField(
        _('Is the exercise available for users'),
        default=False,
    )
    hints_available = models.ManyToManyField(
        'Hint',
        related_name='exercises',
        verbose_name=_('Exercise available hints'),
        blank=True,
    )

    slugify_fields = ('name',)

    class Meta:
        verbose_name = _('Exercise')
        verbose_name_plural = _('Exercises')
        db_table_comment = _("Exercises with user's words")
        ordering = ('-created',)
        get_latest_by = ('created', 'modified')

    def __str__(self) -> str:
        return self.name


class Hint(CreatedModel):
    """Hints available to users for use in exercises."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        _('Hint name'),
        max_length=32,
        unique=True,
    )
    description = models.CharField(
        _('Hint details'),
        max_length=128,
    )
    code = models.CharField(
        _('Hint short code'),
        max_length=32,
        unique=True,
    )

    class Meta:
        verbose_name = _('Hint')
        verbose_name_plural = _('Hints')
        db_table_comment = _('Hints available to users for use in exercises')
        ordering = ('-created',)
        get_latest_by = ('created',)

    def __str__(self) -> str:
        return f'Hint `{self.name}` - {self.description}'


class UsersExercisesHistory(CreatedModel):
    """History details of users passing exercises."""

    FREE_INPUT = 'FI'
    FREE_INPUT_MAX = 'FIM'
    VARIANTS = 'V'
    MODE_OPTIONS = [
        (FREE_INPUT, _('Free input (one translation is enough)')),
        (FREE_INPUT_MAX, _('Free input (maximum translations quantity)')),
        (VARIANTS, _('Choose from variants')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='exercises_history',
    )
    exercise = models.ForeignKey(
        Exercise,
        verbose_name=_('Exercise'),
        on_delete=models.CASCADE,
        related_name='users_history',
    )
    words_amount = models.IntegerField(
        _('Words in exercise amount'),
    )
    corrects_amount = models.IntegerField(
        _('Correct answers amount'),
    )
    incorrects_amount = models.IntegerField(
        _('Incorrect answers amount'),
    )
    answer_time_limit = models.TimeField(
        _('Set time limit'),
        null=True,
        blank=True,
    )
    complete_time = models.TimeField(
        _('The time in which the exercise was completed'),
        null=True,
        blank=True,
    )
    mode = models.CharField(
        _('Exercise chosen mode'),
        max_length=3,
        choices=MODE_OPTIONS,
        default=FREE_INPUT,
    )
    hints_available = models.ManyToManyField(
        'Hint',
        related_name='approaches',
        verbose_name=_('Approach available hints'),
        blank=True,
    )

    class Meta:
        verbose_name = _('User exercise approach')
        verbose_name_plural = _('Users exercise approaches')
        db_table_comment = _('History details of users passing exercises')
        ordering = ('-created',)
        get_latest_by = ('created',)

    def __str__(self) -> str:
        return (
            f'`{self.user}` trained with {self.exercise} at {self.created:%Y-%m-%d} '
            f'({self.words_amount} words)'
        )


class WordsUpdateHistory(CreatedModel, ActivityStatusModel):
    """Words activity status changes history."""

    word = models.ForeignKey(
        'vocabulary.Word',
        verbose_name=_('Word'),
        on_delete=models.CASCADE,
        related_name='update_history',
    )
    activity_status = models.CharField(
        _('Activity status'),
        max_length=8,
        choices=ActivityStatusModel.ACTIVITY,
        blank=False,
        default=ActivityStatusModel.INACTIVE,
    )
    new_activity_status = models.CharField(
        _('New activity status'),
        max_length=8,
        choices=ActivityStatusModel.ACTIVITY,
        blank=False,
        default=ActivityStatusModel.ACTIVE,
    )
    approach = models.ForeignKey(
        UsersExercisesHistory,
        verbose_name=_('Approach'),
        on_delete=models.CASCADE,
        related_name='words_updates',
    )

    class Meta:
        verbose_name = _('Word activity status changes history')
        verbose_name_plural = _('Words activity status changes history')
        db_table_comment = _('Words activity status changes history')
        ordering = ('-created',)
        get_latest_by = ('created',)

    def __str__(self) -> str:
        return (
            f'`{self.word}` word activity status was upgraded from '
            f'{self.activity_status} to {self.new_activity_status}'
        )


class ExerciseHistoryDetails(CreatedModel):
    """History details of users passing some exercise."""

    CORRECT = 'C'
    INCORRECT = 'I'
    SEMI_CORRECT = 'SC'
    VERDICT_OPTIONS = [
        (CORRECT, _('Correct')),
        (INCORRECT, _('Incorrect')),
        (SEMI_CORRECT, _('Semi-correct')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    approach = models.ForeignKey(
        UsersExercisesHistory,
        verbose_name=_('Approach'),
        on_delete=models.CASCADE,
        related_name='details',
    )
    task_word = models.ForeignKey(
        'vocabulary.Word',
        verbose_name=_('Word'),
        on_delete=models.CASCADE,
        related_name='exercises_history',
    )
    task_translation = models.ForeignKey(
        'vocabulary.WordTranslation',
        verbose_name=_('Word translation'),
        on_delete=models.CASCADE,
        related_name='exercises_history',
        null=True,
        blank=True,
    )
    text_answer = models.CharField(
        max_length=MAX_TEXT_ANSWER_LENGTH,
        blank=False,
    )
    verdict = models.CharField(
        max_length=2,
        blank=False,
        choices=VERDICT_OPTIONS,
    )
    suggested_options = models.JSONField(
        blank=True,
        null=True,
    )
    answer_time = models.TimeField(
        _('User answer time'),
        blank=True,
        null=True,
    )
    hints_used = models.ManyToManyField(
        'Hint',
        related_name='history',
        verbose_name=_('Hints used'),
        blank=True,
    )

    class Meta:
        verbose_name = _('Exercise history detail')
        verbose_name_plural = _('Exercise history details')
        db_table_comment = _('History details of users passing some exercise')
        ordering = ('-created',)
        get_latest_by = ('created',)

    def __str__(self) -> str:
        return (
            f'User {self.approach.user} passing exercise {self.approach.exercise} '
            f'detail: word asked - {self.task_word.text}, verdict - {self.verdict}'
        )


class TranslatorUserDefaultSettings(models.Model):
    """Translator exercise settings which are used by default for the user."""

    FROM_LEARNING = 'LTN'
    FROM_NATIVE = 'NTL'
    FROM_LEARNING_TO_LEARNING = 'LTL'
    ALTERNATELY = 'A'
    FROM_LANGUAGE_OPTIONS = [
        (FROM_LEARNING, _('From learning')),
        (FROM_NATIVE, _('From native')),
        (FROM_LEARNING_TO_LEARNING, _('From learning to learning')),
        (ALTERNATELY, _('Alternately')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(
        AUTH_USER_MODEL,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='translator_settings',
    )
    mode = models.CharField(
        _('Exercise chosen mode'),
        max_length=32,
        choices=UsersExercisesHistory.MODE_OPTIONS,
        default=UsersExercisesHistory.FREE_INPUT,
    )
    answer_time_limit = models.TimeField(
        _('Set time limit'),
        null=True,
        blank=True,
    )
    repetitions_amount = models.SmallIntegerField(
        _('Every word repetitions amount'),
        default=1,
    )
    from_language = models.CharField(
        _('Translate from learning or native language'),
        max_length=32,
        choices=FROM_LANGUAGE_OPTIONS,
        default=FROM_LEARNING,
    )

    class Meta:
        verbose_name = _('Translator exercise user default settings')
        verbose_name_plural = _('Translator exercise users default settings')
        db_table_comment = _(
            'Translator exercise settings which are used by default for the user'
        )

    def __str__(self) -> str:
        return f"{self.user}'s `Translator` exercise default settings"


class FavoriteExercise(CreatedModel):
    """Users favorites exercises."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    exercise = models.ForeignKey(
        'Exercise',
        verbose_name=_('Exercise'),
        on_delete=models.CASCADE,
        related_name='favorite_for',
    )
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='favorite_exercises',
    )

    class Meta:
        verbose_name = _('Favorite exercise')
        verbose_name_plural = _('Favorite exercises')
        db_table_comment = _('Users favorite exercises')
        ordering = ('-created',)
        get_latest_by = ('created',)

    def __str__(self) -> str:
        return (
            f'The exercise `{self.exercise}` was added to favorites by '
            f'{self.user} at {self.created}'
        )


class WordSet(
    GetObjectBySlugModelMixin,
    AuthorModel,
    SlugModel,
    CreatedModel,
):
    """
    Sets of words available for the exercise saved by the user for a
    quick start.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        _('Word set name'),
        max_length=ExercisesLengthLimits.MAX_SET_NAME_LENGTH,
    )
    exercise = models.ForeignKey(
        'Exercise',
        verbose_name=_('Exercise'),
        on_delete=models.CASCADE,
        related_name='word_sets',
    )
    last_exercise_date = models.DateTimeField(
        _('Last exercise date'),
        editable=False,
        null=True,
    )
    words = models.ManyToManyField(
        'vocabulary.Word',
        related_name='sets',
        verbose_name=_('Set words'),
        blank=False,
    )

    slugify_fields = ('name', ('exercise', 'name'), ('author', 'username'))

    class Meta:
        verbose_name = _('Word set')
        verbose_name_plural = _('Word sets')
        db_table_comment = _(
            'Sets of words available for the exercise saved by the user for a '
            'quick start'
        )
        ordering = ('-last_exercise_date', '-created')
        get_latest_by = ('created',)

    def __str__(self) -> str:
        return (
            f'`{self.name}` ({self.words.count()} words) set for {self.exercise} '
            f'exercise'
        )


@receiver(pre_save, sender=WordSet)
def fill_slug(sender, instance, *args, **kwargs) -> None:
    """Fills slug field before save instance."""
    slug = slug_filler(sender, instance, *args, **kwargs)
    logger.debug(f'Instance {instance} slug filled with value: {slug}')


@receiver(admin_created, sender=AUTH_USER_MODEL)
def set_exercises_default_settings(sender, instance, *args, **kwargs) -> None:
    """Create default settings for exercises when admin user is created."""
    TranslatorUserDefaultSettings.objects.get_or_create(user=instance)
