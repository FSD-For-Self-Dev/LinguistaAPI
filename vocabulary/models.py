''' Vocabulary models '''

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext as _

from core.models import (
    AuthorModel, CreatedModel, ModifiedModel,
    UserRelatedModel
)
from languages.models import Language
from .utils import slugify_text_author_fields

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        _('Tag name'),
        max_length=64,
        unique=True
    )

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')

    def __str__(self) -> str:
        return self.name


class Collection(CreatedModel, ModifiedModel, AuthorModel):
    title = models.CharField(
        _('Collection title'),
        max_length=256
    )
    description = models.TextField(
        _('Description'),
        max_length=512,
        blank=True
    )
    words = models.ManyToManyField(
        'Word',
        through='WordsInCollections',
        related_name='collections',
        verbose_name=_('Words in collection'),
        blank=True
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Collection')
        verbose_name_plural = _('Collections')

    def __str__(self) -> str:
        return _(f'{self.title} ({self.words.count()} words)')


class Type(models.Model):
    name = models.CharField(
        _('Type name'),
        max_length=64,
        unique=True
    )
    slug = models.SlugField(
        _('Slug'),
        max_length=64,
        unique=True
    )
    sorting = models.PositiveIntegerField(
        _('Sorting order'),
        blank=False,
        null=False,
        default=0,
        help_text=_('increase to show at top of the list')
    )

    @classmethod
    def get_default_pk(cls):
        word_type, created = cls.objects.get_or_create(
            slug='noun',
            defaults={
                'name': _('Noun'),
                'sorting': 3
            },
        )
        return word_type.pk

    class Meta:
        verbose_name = _('Type')
        verbose_name_plural = _('Types')

    def __str__(self) -> str:
        return self.name


class Word(CreatedModel, ModifiedModel):
    ACTIVITY = [
        ('INACTIVE', _('Inactive')),
        ('ACTIVE', _('Active')),
        ('MASTERED', _('Mastered'))
    ]

    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.SET_DEFAULT,
        related_name='words',
        default=Language.get_default_pk
    )
    text = models.CharField(
        _('Word or phrase'),
        max_length=4096
    )
    slug = models.SlugField(
        _('Slug'),
        unique=True,
        max_length=4096
    )
    author = models.ForeignKey(
        User,
        verbose_name=_('Author'),
        on_delete=models.CASCADE,
        related_name='vocabulary'
    )
    type = models.ForeignKey(
        'Type',
        verbose_name=_('Type'),
        on_delete=models.SET_DEFAULT,
        related_name='words',
        default=Type.get_default_pk,
        blank=True,
        null=True
    )
    activity = models.CharField(
        _('Activity status'),
        max_length=8,
        choices=ACTIVITY,
        blank=False,
        default='INACTIVE'
    )
    is_problematic = models.BooleanField(
        _('Is the word problematic for you'),
        default=False
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name=_('Word tags'),
        blank=True
    )
    synonyms = models.ManyToManyField(
        'self',
        through='Synonym',
        symmetrical=True,
        # related_name='synonym_to',
        verbose_name=_('Synonyms'),
        help_text=_('Words with similar meanings'),
        blank=True
    )
    antonyms = models.ManyToManyField(
        'self',
        through='Antonym',
        symmetrical=True,
        # related_name='antonym_to+',
        verbose_name=_('Antonyms'),
        help_text=_('Words with opposite meanings'),
        blank=True
    )
    forms = models.ManyToManyField(
        'self',
        through='Form',
        symmetrical=True,
        # related_name='form_to+',
        verbose_name=_('Forms'),
        help_text=_('Word forms'),
        blank=True
    )
    similars = models.ManyToManyField(
        'self',
        through='Similar',
        symmetrical=True,
        # related_name='similar_to+',
        verbose_name=_('Similars'),
        help_text=_('Words with similar pronunciation or spelling'),
        blank=True
    )
    translations = models.ManyToManyField(
        'Translation',
        through='WordTranslations',
        related_name='translation_for',
        verbose_name=_('Translations'),
        blank=True
    )
    definitions = models.ManyToManyField(
        'Definition',
        through='WordDefinitions',
        related_name='definition_for',
        verbose_name=_('Translations'),
        blank=True
    )
    examples = models.ManyToManyField(
        'UsageExample',
        through='WordUsageExamples',
        related_name='usage_example_for',
        verbose_name=_('Usage Example'),
        blank=True
    )
    # pronunciation_voice = ...

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Word or phrase')
        verbose_name_plural = _('Words and phrases')
        constraints = [
            models.UniqueConstraint(
                fields=['text', 'author'],
                name='unique_words_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        return self.text

    def save(self, *args, **kwargs):
        self.slug = slugify_text_author_fields(self)
        super(Word, self).save(*args, **kwargs)


class WordSelfRelatedModel(CreatedModel):
    from_word = models.ForeignKey(
        Word,
        related_name='%(class)s_from_words',
        on_delete=models.CASCADE
    )
    to_word = models.ForeignKey(
        Word,
        related_name='%(class)s_to_words',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        abstract = True

    def get_classname(self):
        return self.__class__.__name__

    def __str__(self) -> str:
        classname = self.get_classname().lower()
        return '`{from_word}` is {classname} for `{to_word}`'.format(
            from_word=self.from_word, classname=classname, to_word=self.to_word
        )


class WordSelfRelatedWithDifferenceModel(WordSelfRelatedModel, ModifiedModel):
    difference = models.CharField(
        max_length=512,
        verbose_name=_('Difference'),
        help_text=_('Difference between these %(class)ss'),
        blank=True
    )

    class Meta:
        get_latest_by = ['created', 'modified']
        abstract = True

    def __str__(self) -> str:
        if self.difference:
            classname = self.get_classname().lower()
            return (
                '`{from_word}` is {classname} for `{to_word}`'
                '(with a difference in: {difference})'
            ).format(
                from_word=self.from_word, to_word=self.to_word,
                difference=self.difference, classname=classname
            )
        return super().__str__()


class Synonym(WordSelfRelatedWithDifferenceModel, AuthorModel):

    class Meta:
        verbose_name = _('Synonyms')
        verbose_name_plural = _('Synonyms')
        constraints = [
            models.UniqueConstraint(
                fields=['from_word', 'to_word'],
                name='unique_synonym_pair'
            )
        ]


class Antonym(WordSelfRelatedModel, AuthorModel):

    class Meta:
        verbose_name = _('Antonym')
        verbose_name_plural = _('Antonyms')
        constraints = [
            models.UniqueConstraint(
                fields=['from_word', 'to_word'],
                name='unique_antonym_pair'
            )
        ]


class Form(WordSelfRelatedModel, AuthorModel):

    class Meta:
        verbose_name = _('Form')
        verbose_name_plural = _('Forms')
        constraints = [
            models.UniqueConstraint(
                fields=['from_word', 'to_word'],
                name='unique_forms'
            )
        ]


class Similar(WordSelfRelatedModel, AuthorModel):

    class Meta:
        verbose_name = _('Similar')
        verbose_name_plural = _('Similars')
        constraints = [
            models.UniqueConstraint(
                fields=['from_word', 'to_word'],
                name='unique_similars'
            )
        ]


class Translation(CreatedModel, ModifiedModel, AuthorModel):
    text = models.CharField(
        _('Translation'),
        max_length=4096,
        help_text=_('A translation of a word or phrase'),
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Translation')
        verbose_name_plural = _('Translations')
        constraints = [
            models.UniqueConstraint(
                fields=['text', 'author'],
                name='unique_transl_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        return self.text


class WordRelatedModel(CreatedModel):
    word = models.ForeignKey(
        'Word',
        verbose_name=_('Word'),
        on_delete=models.CASCADE,
        related_name='%(class)s'
    )

    class Meta:
        abstract = True


class WordsInCollections(WordRelatedModel):
    collection = models.ForeignKey(
        'Collection',
        verbose_name=_('Collection'),
        on_delete=models.CASCADE,
        related_name='%(class)s'
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Words in collections')
        verbose_name_plural = _('Words in collections')
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'collection'],
                name='unique_word_in_collection'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'Word `{self.word}` was added to collection `{self.collection}` '
            f'at {self.created}'
        )


class WordTranslations(WordRelatedModel):
    translation = models.ForeignKey(
        'Translation',
        verbose_name=_('Translation'),
        on_delete=models.CASCADE,
        related_name='%(class)s'
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Word translation')
        verbose_name_plural = _('Word translations')
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'translation'],
                name='unique_word_translation'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'`{self.word}` is translated as `{self.translation}` '
            f'(translation was added at {self.created})'
        )


class Definition(CreatedModel, ModifiedModel, AuthorModel):
    text = models.CharField(
        _('Definition'),
        max_length=4096,
        help_text=_('A definition of a word or phrase')
    )
    translation = models.CharField(
        _('A translation of the definition'),
        max_length=4096,
        blank=True
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Definition')
        verbose_name_plural = _('Definitions')

    def __str__(self) -> str:
        if self.translation:
            return _(f'{self.text} ({self.translation})')
        return self.text


class WordDefinitions(WordRelatedModel):
    definition = models.ForeignKey(
        'Definition',
        verbose_name=_('Definition'),
        on_delete=models.CASCADE,
        related_name='%(class)s'
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Word definition')
        verbose_name_plural = _('Word definitions')
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'definition'],
                name='unique_word_definition'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'`{self.word}` means `{self.definition}` '
            f'(definition was added at {self.created})'
        )


class UsageExample(CreatedModel, ModifiedModel, AuthorModel):
    text = models.CharField(
        _('Usage example'),
        max_length=4096,
        help_text=_('An usage example of a word or phrase')
    )
    translation = models.CharField(
        _('A translation of the example'),
        max_length=4096,
        blank=True
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Usage example')
        verbose_name_plural = _('Usage examples')

    def __str__(self) -> str:
        if self.translation:
            return _(f'{self.text} ({self.translation})')
        return self.text


class WordUsageExamples(WordRelatedModel):
    example = models.ForeignKey(
        'UsageExample',
        verbose_name=_('Usage example'),
        on_delete=models.CASCADE,
        related_name='%(class)s'
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Word usage example')
        verbose_name_plural = _('Word usage examples')
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'example'],
                name='unique_word_example'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'Usage example of `{self.word}`: {self.example} '
            f'(example was added at {self.created})'
        )


class Note(WordRelatedModel):
    text = models.CharField(
        _('Note text'),
        max_length=4096
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')

    def __str__(self) -> str:
        return _(
            f'Note to the word `{self.word}`: {self.text} '
            f'(note was added at {self.created})'
        )


class ImageAssociation(WordRelatedModel):
    image = models.ImageField(
        _('Image'),
        upload_to='words/associations/images',
        null=True,
        blank=True,
        help_text=_('Image association'),
    )
    name = models.CharField(
        _('Image name'),
        max_length=64,
        blank=True
    )

    class Meta:
        verbose_name = _('Association image')
        verbose_name_plural = _('Association images')

    def __str__(self) -> str:
        if self.name:
            return _(f'Image `{self.name}` for `{self.word}`')
        return _(f'Image for `{self.word}`')


class FavoriteWord(UserRelatedModel):
    word = models.ForeignKey(
        'Word',
        verbose_name=_('Word'),
        on_delete=models.CASCADE,
        related_name='favorite_for'
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Favorite word')
        verbose_name_plural = _('Favorite words')

    def __str__(self) -> str:
        return _(
            f'The word `{self.word}` was added to favorites by '
            f'{self.user} at {self.created}'
        )


class FavoriteCollection(UserRelatedModel):
    collection = models.ForeignKey(
        'Collection',
        verbose_name=_('Collection'),
        on_delete=models.CASCADE,
        related_name='favorite_for'
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Favorite collection')
        verbose_name_plural = _('Favorite collections')

    def __str__(self) -> str:
        return _(
            f'The collection `{self.collection}` was added to favorites by '
            f'{self.user} at {self.created}'
        )
