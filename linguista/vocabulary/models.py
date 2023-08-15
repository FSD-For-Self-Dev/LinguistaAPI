""" Vocabulary models """

from django.conf.global_settings import LANGUAGES
from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreatedModel, ModifiedModel

User = get_user_model()


class Tag(models.Model):
    """Тег"""

    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Тег',
        help_text='Добавьте тег'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tags',
        verbose_name='Автор'
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Collection(CreatedModel, ModifiedModel):
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
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='collections',
        verbose_name='Автор'
    )

    def __str__(self) -> str:
        return self.title

    class Meta:
        verbose_name = 'Коллекция'
        verbose_name_plural = 'Коллекции'


class Word(CreatedModel, ModifiedModel):
    """Слово/фраза"""

    STATUS = [
        ('PROBLEM', 'Проблемное'),
        ('USEFUL', 'Важное'),
        ('MASTERED', 'Усвоенное'),
    ]
    TYPE = [
        ('NOUN', 'Существительное'),
        ('VERB', 'Глагол'),
        ('ADJECT', 'Прилагательное'),
        ('ADVERB', 'Наречие'),
        ('PRONOUN', 'Местоимение'),
        ('PRETEXT', 'Предлог'),
        ('UNION', 'Союз'),
        ('PARTICLE', 'Частица'),
        ('PARTICIPLE', 'Причастие'),
        ('GERUND', 'Деепричастие'),
        ('ARTICLE', 'Артикль'),
        ('PREDICATIVE', 'Предикатив'),
        ('NUMERAL', 'Числительное'),
        ('INTERJ', 'Междометие'),
        ('PHRASE', 'Фраза'),
        ('IDIOM', 'Идиома'),
        ('QUOTE', 'Цитата'),
    ]

    language = models.CharField(max_length=7, choices=LANGUAGES)
    text = models.CharField(
        max_length=512,
        unique=True,
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
        related_name='vocabulary',
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        help_text='Добавьте теги к слову',
        blank=True
    )
    status = models.CharField(
        max_length=8,
        choices=STATUS,
        blank=True
    )
    type = models.CharField(
        max_length=11,
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
    # foo = models.ImageField(
    #     upload_to='words/',
    #     null=True
    # )
    # synonyms = models.ManyToManyField(
    #     'self',
    #     through='Synonym',
    #     symmetrical = True,
    #     verbose_name='Синонимы',
    #     help_text='Укажите синонимы слова',
    #     blank=True
    # )

    def __str__(self) -> str:
        return self.text
    
    class Meta:
        ordering = ['-created']
        get_latest_by = ["created", "modified"]
        verbose_name = 'Слово или фраза'
        verbose_name_plural = 'Слова и фразы'


class Translation(CreatedModel, ModifiedModel):
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
    
    class Meta:
        verbose_name = 'Перевод'
        verbose_name_plural = 'Переводы'


class UsageExample(CreatedModel, ModifiedModel):
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

    class Meta:
        verbose_name = 'Пример использования'
        verbose_name_plural = 'Примеры использования'


# class Synonym(models.Model):
#     word = models.ForeignKey(
#         Word,
#         related_name='synonyms_info',
#         on_delete=models.CASCADE
#     )
#     synonym = models.ForeignKey(
#         Word,
#         related_name='+',
#         on_delete=models.CASCADE
#     )
#     note = models.CharField(
#         max_length=512,
#         verbose_name='Примечание',
#         help_text='Добавьте примечание, например, объяснение разницы',
#         blank=True
#     )

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(
    #             fields=['word1', 'word2'],
    #             name='unique_word_synonym'
    #         )
    #     ]

    # def __str__(self) -> str:
    #     return f'{self.synonym} является синонимом {self.word}'


class WordCollection(CreatedModel):
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

    class Meta:
        verbose_name = 'Слово в коллекции'
        verbose_name_plural = 'Слова в коллекции'


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
    
    class Meta:
        verbose_name = 'Упражнение'
        verbose_name_plural = 'Упражнения'
