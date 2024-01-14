"""Exercises models."""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from core.models import CreatedModel, ModifiedModel

User = get_user_model()


class Exercise(CreatedModel, ModifiedModel):
    name = models.CharField(_('Exercise name'), max_length=256)
    description = models.CharField(_('Description'), max_length=4096)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Exercise')
        verbose_name_plural = _('Exercises')


class FavoriteExercise(CreatedModel):
    exercise = models.ForeignKey(
        'Exercise',
        verbose_name=_('Exercise'),
        on_delete=models.CASCADE,
        related_name='favorite_for',
    )
    user = models.ForeignKey(
        User,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='favorite_exercises',
    )

    def __str__(self) -> str:
        return _(
            f'The exercise `{self.exercise}` was added to favorites by '
            f'{self.user} at {self.created}'
        )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Favorite exercise')
        verbose_name_plural = _('Favorite exercises')
