"""Модели приложения vocabulary."""

from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.text import slugify
from django.utils.translation import gettext as _

from core.models import AuthorModel, CreatedModel, ModifiedModel, UserRelatedModel
from languages.models import Language

from .constants import (
    MAX_COLLECTION_DESCRIPTION_LENGTH,
    MAX_COLLECTION_NAME_LENGTH,
    MAX_DEFINITION_LENGTH,
    MAX_EXAMPLE_LENGTH,
    MAX_FORMSGROUP_NAME_LENGTH,
    MAX_IMAGE_NAME_LENGTH,
    MAX_NOTE_LENGTH,
    MAX_TAG_LENGTH,
    MAX_TRANSLATION_LENGTH,
    MAX_WORD_LENGTH,
    MIN_COLLECTION_NAME_LENGTH,
    MIN_DEFINITION_LENGTH,
    MIN_EXAMPLE_LENGTH,
    MIN_FORMSGROUP_NAME_LENGTH,
    MIN_TAG_LENGTH,
    MIN_TRANSLATION_LENGTH,
    MIN_WORD_LENGTH,
    REGEX_MESSAGE,
    REGEX_TEXT_MASK,
)
from .utils import slugify_text_author_fields

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        _('Tag name'),
        max_length=MAX_TAG_LENGTH,
        unique=True,
        validators=(
            MinLengthValidator(MIN_TAG_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_MESSAGE),
        ),
    )

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')

    def __str__(self) -> str:
        return self.name


class Collection(CreatedModel, ModifiedModel, AuthorModel):
    title = models.CharField(
        _('Collection title'),
        max_length=MAX_COLLECTION_NAME_LENGTH,
        validators=(
            MinLengthValidator(MIN_COLLECTION_NAME_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_MESSAGE),
        ),
    )
    slug = models.SlugField(_('Slug'), null=True, unique=True)
    description = models.TextField(
        _('Description'), max_length=MAX_COLLECTION_DESCRIPTION_LENGTH, blank=True
    )
    words = models.ManyToManyField(
        'Word',
        through='WordsInCollections',
        related_name='collections',
        verbose_name=_('Word in collection'),
        blank=True,
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Collection')
        verbose_name_plural = _('Collections')
        constraints = [
            models.UniqueConstraint(
                Lower('title'), 'author', name='unique_user_collection'
            )
        ]

    def __str__(self) -> str:
        return _(f'{self.title} ({self.words.count()} words)')

    def words_count(self) -> int:
        return self.words.count()  # *

    def save(self, *args, **kwargs):
        self.slug = slugify_text_author_fields(self, self.title)
        super(Collection, self).save(*args, **kwargs)


class Type(models.Model):
    name = models.CharField(
        _('Type name'),
        max_length=64,
        unique=True,
        validators=(
            MinLengthValidator(1),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_MESSAGE),
        ),
    )
    slug = models.SlugField(_('Slug'), max_length=64, unique=True)
    sorting = models.PositiveIntegerField(
        _('Sorting order'),
        blank=False,
        null=False,
        default=0,
        help_text=_('increase to show at top of the list'),
    )

    @classmethod
    def get_default_pk(cls):
        word_type, created = cls.objects.get_or_create(
            slug='noun',
            defaults={'name': _('Noun'), 'sorting': 3},
        )
        return word_type.pk

    class Meta:
        verbose_name = _('Type')
        verbose_name_plural = _('Types')

    def __str__(self) -> str:
        return self.name


class Word(CreatedModel, ModifiedModel):
    INACTIVE = 'I'
    ACTIVE = 'A'
    MASTERED = 'M'
    ACTIVITY = [
        (INACTIVE, _('Inactive')),
        (ACTIVE, _('Active')),
        (MASTERED, _('Mastered')),
    ]

    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.SET_DEFAULT,
        related_name='words',
        default=Language.get_default_pk,
    )
    text = models.CharField(
        _('Word or phrase'),
        blank=False,
        max_length=MAX_WORD_LENGTH,
        validators=(
            MinLengthValidator(MIN_WORD_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_MESSAGE),
        ),
    )
    slug = models.SlugField(_('Slug'), unique=True, max_length=4096)
    author = models.ForeignKey(
        User,
        verbose_name=_('Author'),
        on_delete=models.CASCADE,
        related_name='vocabulary',
    )
    types = models.ManyToManyField(
        'Type', verbose_name=_('Type'), related_name='words', blank=True
    )
    activity = models.CharField(
        _('Activity status'),
        max_length=8,
        choices=ACTIVITY,
        blank=False,
        default=INACTIVE,
    )
    is_problematic = models.BooleanField(
        _('Is the word problematic for you'), default=False
    )
    tags = models.ManyToManyField(
        'Tag', verbose_name=_('Word tags'), related_name='words', blank=True
    )
    synonyms = models.ManyToManyField(
        'self',
        through='Synonym',
        symmetrical=True,
        verbose_name=_('Synonyms'),
        help_text=_('Words with similar meanings'),
        blank=True,
    )
    antonyms = models.ManyToManyField(
        'self',
        through='Antonym',
        symmetrical=True,
        verbose_name=_('Antonyms'),
        help_text=_('Words with opposite meanings'),
        blank=True,
    )
    forms = models.ManyToManyField(
        'self',
        through='Form',
        symmetrical=True,
        verbose_name=_('Forms'),
        help_text=_('Word forms'),
        blank=True,
    )
    similars = models.ManyToManyField(
        'self',
        through='Similar',
        symmetrical=True,
        verbose_name=_('Similars'),
        help_text=_('Words with similar pronunciation or spelling'),
        blank=True,
    )
    translations = models.ManyToManyField(
        'WordTranslation',
        through='WordTranslations',
        related_name='translation_for',
        verbose_name=_('Translations'),
        blank=True,
    )
    definitions = models.ManyToManyField(
        'Definition',
        through='WordDefinitions',
        related_name='definition_for',
        verbose_name=_('Definitions'),
        blank=True,
    )
    examples = models.ManyToManyField(
        'UsageExample',
        through='WordUsageExamples',
        related_name='usage_example_for',
        verbose_name=_('Usage example'),
        blank=True,
    )
    # pronunciation_voice = ...

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Word or phrase')
        verbose_name_plural = _('Words and phrases')
        constraints = [
            models.UniqueConstraint('text', 'author', name='unique_words_in_user_voc')
        ]

    def __str__(self) -> str:
        return self.text

    @staticmethod
    def get_slug(text, author_id):
        return slugify_text_author_fields(text, author_id)

    def save(self, *args, **kwargs):
        self.slug = self.get_slug(self.text, self.author.id)
        super(Word, self).save(*args, **kwargs)
        default_type_pk = Type.get_default_pk()
        self.types.add(default_type_pk)  # *


class WordSelfRelatedModel(CreatedModel):
    to_word = models.ForeignKey(
        Word, related_name='%(class)s_to_words', on_delete=models.CASCADE
    )
    from_word = models.ForeignKey(
        Word, related_name='%(class)s_from_words', on_delete=models.CASCADE
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
        blank=True,
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        abstract = True

    def __str__(self) -> str:
        if self.difference:
            classname = self.get_classname().lower()
            return (
                '`{from_word}` is {classname} for `{to_word}`'
                '(with a difference in: {difference})'
            ).format(
                from_word=self.from_word,
                to_word=self.to_word,
                difference=self.difference,
                classname=classname,
            )
        return super().__str__()


class Synonym(WordSelfRelatedWithDifferenceModel, AuthorModel):
    class Meta:
        ordering = ['-created']  # повтор
        get_latest_by = ['created', 'modified']
        verbose_name = _('Synonyms')
        verbose_name_plural = _('Synonyms')
        constraints = [
            models.UniqueConstraint(
                fields=['from_word', 'to_word'], name='unique_synonym_pair'
            )
        ]


class Antonym(WordSelfRelatedModel, AuthorModel):
    class Meta:
        verbose_name = _('Antonym')
        verbose_name_plural = _('Antonyms')
        constraints = [
            models.UniqueConstraint(
                fields=['from_word', 'to_word'], name='unique_antonym_pair'
            )
        ]


class FormsGroup(AuthorModel, CreatedModel, ModifiedModel):
    name = models.CharField(
        _('Group name'),
        max_length=MAX_FORMSGROUP_NAME_LENGTH,
        blank=False,
        validators=(
            MinLengthValidator(MIN_FORMSGROUP_NAME_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_MESSAGE),
        ),
    )
    slug = models.SlugField(_('Slug'), null=True, unique=True)
    words = models.ManyToManyField(
        'Word',
        through='WordsFormGroups',
        related_name='forms_groups',
        verbose_name=_('Words in forms group'),
        blank=True,
    )

    class Meta:
        verbose_name = _('Forms group')
        verbose_name_plural = _('Forms groups')
        ordering = ('-created', 'name')
        constraints = [
            models.UniqueConstraint(Lower('name'), 'author', name='unique_group_name')
        ]

    def __str__(self):
        return f'{self.name}'

    def save(self, *args, **kwargs):
        self.slug = slugify([self.name, self.author])
        self.name = self.name.capitalize()
        super(FormsGroup, self).save(*args, **kwargs)


class Form(WordSelfRelatedModel, AuthorModel):
    class Meta:
        verbose_name = _('Form')
        verbose_name_plural = _('Forms')
        constraints = [
            models.UniqueConstraint(
                fields=['from_word', 'to_word'], name='unique_forms'
            )
        ]


class Similar(WordSelfRelatedModel, AuthorModel):
    class Meta:
        verbose_name = _('Similar')
        verbose_name_plural = _('Similars')
        constraints = [
            models.UniqueConstraint(
                fields=['from_word', 'to_word'], name='unique_similars'
            )
        ]


class WordTranslation(CreatedModel, ModifiedModel, AuthorModel):
    text = models.CharField(
        _('Translation'),
        max_length=MAX_TRANSLATION_LENGTH,
        help_text=_('A translation of a word or phrase'),
        validators=(
            MinLengthValidator(MIN_TRANSLATION_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_MESSAGE),
        ),
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.SET_DEFAULT,
        related_name='words_translations',
        default=Language.get_default_pk,
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Translation')
        verbose_name_plural = _('Translations')
        constraints = [
            models.UniqueConstraint(
                Lower('text'), 'author', name='unique_word_translation_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        return self.text


class WordRelatedModel(CreatedModel):
    word = models.ForeignKey(
        'Word',
        verbose_name=_('Word'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    class Meta:
        abstract = True


class WordsFormGroups(WordRelatedModel):
    forms_group = models.ForeignKey(
        FormsGroup,
        verbose_name=_('Forms group'),
        null=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s',
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Words forms group')
        verbose_name_plural = _('Words forms group')
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'forms_group'], name='unique_word_forms_group'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'Word `{self.word}` ({self.word.language.name}) is in '
            f'`{self.forms_group}` form'
        )


class WordsInCollections(WordRelatedModel):
    collection = models.ForeignKey(
        'Collection',
        verbose_name=_('Collection'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Words in collections')
        verbose_name_plural = _('Words in collections')
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'collection'], name='unique_word_in_collection'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'Word `{self.word}` ({self.word.language.name}) was added to '
            f'collection `{self.collection}` at {self.created:%Y-%m-%d}'
        )


class WordTranslations(WordRelatedModel):
    translation = models.ForeignKey(
        'WordTranslation',
        verbose_name=_('Translation'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Word translation')
        verbose_name_plural = _('Word translations')
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'translation'], name='unique_word_translation'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'`{self.word}` ({self.word.language.name}) is translated as '
            f'`{self.translation}` ({self.translation.language.name}) '
            f'(translation was added at {self.created:%Y-%m-%d})'
        )


class Definition(CreatedModel, ModifiedModel, AuthorModel):
    text = models.CharField(
        _('Definition'),
        max_length=MAX_DEFINITION_LENGTH,
        help_text=_('A definition of a word or phrase'),
        validators=(
            MinLengthValidator(MIN_DEFINITION_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_MESSAGE),
        ),
    )
    translation = models.CharField(
        _('A translation of the definition'),
        max_length=MAX_DEFINITION_LENGTH,
        blank=True,
        validators=(
            MinLengthValidator(MIN_DEFINITION_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_MESSAGE),
        ),
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Definition')
        verbose_name_plural = _('Definitions')
        constraints = [
            models.UniqueConstraint(
                Lower('text'), 'author', name='unique_definition_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        if self.translation:
            return _(f'{self.text} ({self.translation})')
        return self.text


class WordDefinitions(WordRelatedModel):
    definition = models.ForeignKey(
        'Definition',
        verbose_name=_('Definition'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Word definition')
        verbose_name_plural = _('Word definitions')
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'definition'], name='unique_word_definition'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'`{self.word}` ({self.word.language.name}) means '
            f'`{self.definition}` (definition was added at '
            f'{self.created:%Y-%m-%d})'
        )


class UsageExample(CreatedModel, ModifiedModel, AuthorModel):
    text = models.CharField(
        _('Usage example'),
        max_length=MAX_EXAMPLE_LENGTH,
        help_text=_('An usage example of a word or phrase'),
        validators=(
            MinLengthValidator(MIN_EXAMPLE_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_MESSAGE),
        ),
    )
    translation = models.CharField(
        _('A translation of the example'),
        max_length=MAX_EXAMPLE_LENGTH,
        blank=True,
        validators=(
            MinLengthValidator(MIN_EXAMPLE_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_MESSAGE),
        ),
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Usage example')
        verbose_name_plural = _('Usage examples')
        constraints = [
            models.UniqueConstraint(
                Lower('text'), 'author', name='unique_word_usage_example_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        if self.translation:
            return _(f'{self.text} ({self.translation})')
        return self.text


class WordUsageExamples(WordRelatedModel):
    example = models.ForeignKey(
        'UsageExample',
        verbose_name=_('Usage example'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Word usage example')
        verbose_name_plural = _('Word usage examples')
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'example'], name='unique_word_example'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'Usage example of `{self.word}`: {self.example} '
            f'(example was added at {self.created:%Y-%m-%d})'
        )


class Note(CreatedModel, ModifiedModel):
    word = models.ForeignKey(
        'Word', verbose_name=_('Word'), on_delete=models.CASCADE, related_name='notes'
    )
    text = models.CharField(_('Note text'), max_length=MAX_NOTE_LENGTH, blank=False)

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')

    def __str__(self) -> str:
        return _(
            f'Note to the word `{self.word}`: {self.text} '
            f'(note was added at {self.created:%Y-%m-%d})'
        )


class ImageAssociation(CreatedModel, ModifiedModel):
    word = models.ForeignKey(
        'Word', verbose_name=_('Word'), on_delete=models.CASCADE, related_name='images'
    )
    image = models.ImageField(
        _('Image'),
        upload_to='words/associations/images',
        null=True,
        blank=True,
        help_text=_('Image association'),
    )
    name = models.CharField(
        _('Image name'),
        max_length=MAX_IMAGE_NAME_LENGTH,
        blank=True,
        validators=(RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_MESSAGE),),
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
        related_name='favorite_for',
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Favorite word')
        verbose_name_plural = _('Favorite words')

    def __str__(self) -> str:
        return _(
            f'The word `{self.word}` was added to favorites by '
            f'{self.user} at {self.created:%Y-%m-%d}'
        )


class FavoriteCollection(UserRelatedModel):
    collection = models.ForeignKey(
        'Collection',
        verbose_name=_('Collection'),
        on_delete=models.CASCADE,
        related_name='favorite_for',
    )

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Favorite collection')
        verbose_name_plural = _('Favorite collections')

    def __str__(self) -> str:
        return _(
            f'The collection `{self.collection}` was added to favorites by '
            f'{self.user} at {self.created:%Y-%m-%d}'
        )
