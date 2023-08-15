''' Exercises app config '''

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import CreatedModel, ModifiedModel, UserRelatedModel

class Exercise(CreatedModel, ModifiedModel):
    '''Упражнение'''

    name = models.CharField(
        max_length=256,
        verbose_name='Название',
        help_text='Дайте название упражнению'
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Опишите упражнение'
    )

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        verbose_name = 'Упражнение'
        verbose_name_plural = 'Упражнения'


class FavoriteExercise(UserRelatedModel):
    exercise = models.ForeignKey(
        'Exercise',
        verbose_name=_('Exercise'),
        on_delete=models.CASCADE,
        related_name='favorite_for'
    )

    def __str__(self) -> str:
        return _(
            f'The exercise `{self.exercise}` was added to favorites by '
            f'{self.user} at {self.created}'
        )

    class Meta:
        ordering = ['-created']
        get_latest_by = ["created"]
        verbose_name = _('Favorite exercise')
        verbose_name_plural = _('Favorite exercises')
