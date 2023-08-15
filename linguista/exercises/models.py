''' Exercises app config '''

from django.db import models


class Exercise(models.Model):
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
        return f'{self.name}: {self.description}'
    
    class Meta:
        verbose_name = 'Упражнение'
        verbose_name_plural = 'Упражнения'
