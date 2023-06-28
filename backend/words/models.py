from django.conf.global_settings import LANGUAGES
from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModifiedModel

User = get_user_model()


class Tag(models.Model):
    """Тег"""
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Тег',
        help_text='Добавьте тег'
    )

    def __str__(self) -> str:
        return self.name


class Collection(CreatedModifiedModel):
    """Коллекция"""
    title = models.CharField(
        max_length=256,
        verbose_name='Название',
        help_text='Дайте название коллекции'
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Опишите коллекцию',
        blank=True
    )

    def __str__(self) -> str:
        return self.title


class Word(CreatedModifiedModel):
    """Слово"""
    PROBLEM = 'P'
    USEFUL = 'U'
    MASTERED = 'M'
    STATUS = [
        (PROBLEM, 'Проблемное'),
        (USEFUL, 'Важное'),
        (MASTERED, 'Усвоенное'),
    ]
    WORD = 'W'
    PHRASE = 'P'
    QUOTE = 'Q'
    TYPE = [
        (WORD, 'Слово'),
        (PHRASE, 'Фраза'),
        (QUOTE, 'Цитата'),
    ]

    language = models.CharField(max_length=7, choices=LANGUAGES)
    text = models.CharField(
        max_length=512,
        verbose_name='Слово/фраза',
        help_text='Введите слово/фразу'
    )
    note = models.CharField(
        max_length=512,
        verbose_name='Примечание',
        help_text='Добавьте примечание',
        blank=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='words',
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        help_text='Добавьте теги к слову'
    )
    status = models.CharField(
        max_length=1,
        choices=STATUS,
        blank=True
    )
    type = models.CharField(
        max_length=1,
        choices=TYPE,
        blank=True
    )
    collections = models.ManyToManyField(
        Collection,
        through='WordCollection',
        related_name='words',
        verbose_name='Коллекции',
        help_text='Добавьте слово в коллекцию'
    )

    def __str__(self) -> str:
        return self.text


class Translation(CreatedModifiedModel):
    """Перевод"""
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='translations',
        verbose_name='Слово'
    )
    translation = models.CharField(
        max_length=512,
        verbose_name='Перевод',
        help_text='Введите перевод слова/фразы'
    )
    definition = models.CharField(
        max_length=512,
        verbose_name='Определение',
        help_text='Добавьте определение',
        blank=True
    )
    definition_translation = models.CharField(
        max_length=512,
        verbose_name='Перевод определения',
        help_text='Добавьте перевод определения',
        blank=True
    )

    def __str__(self) -> str:
        return f'Перевод слова/фразы {self.word}: {self.translation}'


class UsageExample(CreatedModifiedModel):
    """Пример использования"""
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='examples',
        verbose_name='Слово'
    )
    example = models.CharField(
        max_length=512,
        verbose_name='Пример использования слова/фразы',
        help_text='Добавьте пример использования слова/фразы в предложении'
    )
    translation = models.CharField(
        max_length=512,
        verbose_name='Перевод',
        help_text='Введите перевод примера',
        blank=True
    )

    def __str__(self) -> str:
        return f'Пример использования слова/фразы {self.word}: {self.example}'


class WordCollection(CreatedModifiedModel):
    """Слова в коллекции"""
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE
    )
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'collection'],
                name='unique_word_collection'
            )
        ]

    def __str__(self) -> str:
        return f'Слово {self.word} есть в коллекции {self.collection}'


class Exercise(models.Model):
    """Упражнение"""
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
