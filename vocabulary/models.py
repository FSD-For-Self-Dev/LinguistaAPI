"""Модели приложения vocabulary."""

import uuid

from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext as _

from core.models import (
    GetObjectBySlugModelMixin,
    GetObjectModelMixin,
    CreatedModel,
    ModifiedModel,
    SlugModel,
    slug_filler,
)
from languages.models import Language

from .constants import (
    LengthLimits,
    REGEX_TEXT_MASK_DETAIL,
    REGEX_TEXT_MASK,
    REGEX_HEXCOLOR_MASK,
    REGEX_HEXCOLOR_MASK_DETAIL,
)

User = get_user_model()


class WordsCountMixin:
    def words_count(self) -> int:
        return self.words.count()


class UserRelatedModel(CreatedModel):
    user = models.ForeignKey(
        User, verbose_name=_('User'), on_delete=models.CASCADE, related_name='%(class)s'
    )

    class Meta:
        abstract = True


class AuthorModel(models.Model):
    author = models.ForeignKey(
        User,
        verbose_name=_('Author'),
        on_delete=models.CASCADE,
        related_name='%(class)ss',
    )

    class Meta:
        abstract = True


class Word(
    GetObjectBySlugModelMixin,
    SlugModel,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    INACTIVE = 'I'
    ACTIVE = 'A'
    MASTERED = 'M'
    ACTIVITY = [
        (INACTIVE, _('Inactive')),
        (ACTIVE, _('Active')),
        (MASTERED, _('Mastered')),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
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
        max_length=LengthLimits.MAX_WORD_LENGTH,
        validators=(
            MinLengthValidator(LengthLimits.MIN_WORD_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    activity_status = models.CharField(
        _('Activity status'),
        max_length=8,
        choices=ACTIVITY,
        blank=False,
        default=INACTIVE,
    )
    is_problematic = models.BooleanField(
        _('Is the word problematic for you'),
        default=False,
    )
    types = models.ManyToManyField(
        'Type',
        verbose_name=_('Type'),
        related_name='words',
        blank=True,
    )
    tags = models.ManyToManyField(
        'Tag',
        verbose_name=_('Word tags'),
        related_name='words',
        blank=True,
    )
    forms_groups = models.ManyToManyField(
        'FormsGroup',
        through='WordsFormGroups',
        related_name='words',
        verbose_name=_('Word form groups'),
        blank=True,
    )
    translations = models.ManyToManyField(
        'WordTranslation',
        through='WordTranslations',
        related_name='words',
        verbose_name=_('Translations'),
        blank=True,
    )
    definitions = models.ManyToManyField(
        'Definition',
        through='WordDefinitions',
        related_name='words',
        verbose_name=_('Definitions'),
        blank=True,
    )
    examples = models.ManyToManyField(
        'UsageExample',
        through='WordUsageExamples',
        related_name='words',
        verbose_name=_('Usage example'),
        blank=True,
    )
    images_associations = models.ManyToManyField(
        'ImageAssociation',
        through='WordImageAssociations',
        related_name='words',
        verbose_name=_('Image association'),
        blank=True,
    )
    quotes_associations = models.ManyToManyField(
        'QuoteAssociation',
        through='WordQuoteAssociations',
        related_name='words',
        verbose_name=_('Quote association'),
        blank=True,
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
    last_exercise_date = models.DateTimeField(
        _('Last exercise date'),
        editable=False,
        null=True,
    )

    slugify_fields = ('text', ('author', 'username'))

    class Meta:
        verbose_name = _('Word or phrase')
        verbose_name_plural = _('Words and phrases')
        ordering = ('-created', '-modified', '-id')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint('text', 'author', name='unique_words_in_user_voc')
        ]

    def __str__(self) -> str:
        return f'{self.text} (by {self.author})'


class Type(
    GetObjectBySlugModelMixin,
    WordsCountMixin,
    SlugModel,
    CreatedModel,
    ModifiedModel,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        _('Type name'),
        max_length=64,
        unique=True,
        validators=(
            MinLengthValidator(1),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    slugify_fields = ('name',)

    class Meta:
        verbose_name = _('Type')
        verbose_name_plural = _('Types')
        ordering = ('-created', '-modified', '-id')
        get_latest_by = ('created', 'modified')

    def __str__(self) -> str:
        return f'{self.name}'


class Tag(
    GetObjectModelMixin,
    WordsCountMixin,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        _('Tag name'),
        max_length=LengthLimits.MAX_TAG_LENGTH,
        unique=True,
        validators=(
            MinLengthValidator(LengthLimits.MIN_TAG_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    get_object_by_fields = ('name', 'author')

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ('-created', '-modified')
        get_latest_by = ('created', 'modified')

    def __str__(self) -> str:
        return f'{self.name} (by {self.author})'


class FormsGroup(
    GetObjectBySlugModelMixin,
    WordsCountMixin,
    SlugModel,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        _('Group name'),
        max_length=LengthLimits.MAX_FORMSGROUP_NAME_LENGTH,
        blank=False,
        validators=(
            MinLengthValidator(LengthLimits.MIN_FORMSGROUP_NAME_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.SET_DEFAULT,
        related_name='forms_groups',
        default=Language.get_default_pk,
    )
    color = models.CharField(
        _('Group color'),
        max_length=7,
        blank=True,
        validators=(
            MinLengthValidator(7),
            RegexValidator(
                regex=REGEX_HEXCOLOR_MASK, message=REGEX_HEXCOLOR_MASK_DETAIL
            ),
        ),
    )
    translation = models.CharField(
        _('Group name translation'),
        max_length=LengthLimits.MAX_FORMSGROUP_NAME_LENGTH,
        blank=True,
        validators=(
            MinLengthValidator(LengthLimits.MIN_FORMSGROUP_NAME_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    slugify_fields = ('name', ('author', 'username'))

    class Meta:
        verbose_name = _('Forms group')
        verbose_name_plural = _('Forms groups')
        ordering = ('-created', '-modified', 'name')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(Lower('name'), 'author', name='unique_group_name')
        ]

    def __str__(self):
        return f'{self.name}'

    def save(self, *args, **kwargs):
        self.name = self.name.capitalize()
        super(FormsGroup, self).save(*args, **kwargs)


class WordTranslation(
    GetObjectBySlugModelMixin,
    WordsCountMixin,
    SlugModel,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    text = models.CharField(
        _('Translation'),
        max_length=LengthLimits.MAX_TRANSLATION_LENGTH,
        help_text=_('A translation of a word or phrase'),
        validators=(
            MinLengthValidator(LengthLimits.MIN_TRANSLATION_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.SET_DEFAULT,
        related_name='word_translations',
        default=Language.get_default_pk,
    )

    slugify_fields = ('text', ('author', 'username'))

    class Meta:
        verbose_name = _('Translation')
        verbose_name_plural = _('Translations')
        ordering = ('-created', '-modified')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(
                Lower('text'), 'author', name='unique_word_translation_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        return f'{self.text} ({self.language})'


class Definition(
    GetObjectBySlugModelMixin,
    WordsCountMixin,
    SlugModel,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    text = models.CharField(
        _('Definition'),
        max_length=LengthLimits.MAX_DEFINITION_LENGTH,
        help_text=_('A definition of a word or phrase'),
        validators=(
            MinLengthValidator(LengthLimits.MIN_DEFINITION_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.SET_DEFAULT,
        related_name='definitions',
        default=Language.get_default_pk,
    )
    translation = models.CharField(
        _('A translation of the definition'),
        max_length=LengthLimits.MAX_DEFINITION_LENGTH,
        blank=True,
        validators=(
            MinLengthValidator(LengthLimits.MIN_DEFINITION_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    slugify_fields = ('text', ('author', 'username'))

    class Meta:
        verbose_name = _('Definition')
        verbose_name_plural = _('Definitions')
        ordering = ('-created', '-modified', '-id')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(
                Lower('text'), 'author', name='unique_definition_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        if self.translation:
            return _(f'{self.text} ({self.translation})')
        return self.text


class UsageExample(
    GetObjectBySlugModelMixin,
    WordsCountMixin,
    SlugModel,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    text = models.CharField(
        _('Usage example'),
        max_length=LengthLimits.MAX_EXAMPLE_LENGTH,
        help_text=_('An usage example of a word or phrase'),
        validators=(
            MinLengthValidator(LengthLimits.MIN_EXAMPLE_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.SET_DEFAULT,
        related_name='examples',
        default=Language.get_default_pk,
    )
    translation = models.CharField(
        _('A translation of the example'),
        max_length=LengthLimits.MAX_EXAMPLE_LENGTH,
        blank=True,
        validators=(
            MinLengthValidator(LengthLimits.MIN_EXAMPLE_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    slugify_fields = ('text', ('author', 'username'))

    class Meta:
        verbose_name = _('Usage example')
        verbose_name_plural = _('Usage examples')
        ordering = ('-created', '-modified')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(
                Lower('text'), 'author', name='unique_word_usage_example_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        if self.translation:
            return _(f'{self.text} ({self.translation})')
        return self.text


class ImageAssociation(
    GetObjectModelMixin,
    WordsCountMixin,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    image = models.ImageField(
        _('Image'),
        upload_to='vocabulary/associations/images',
        null=False,
        blank=False,
    )
    name = models.CharField(
        _('Image name'),
        max_length=LengthLimits.MAX_IMAGE_NAME_LENGTH,
        blank=True,
        validators=(
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    get_object_by_fields = ('image',)

    class Meta:
        ordering = ('-created', '-modified')
        get_latest_by = ('created', 'modified')
        verbose_name = _('Association image')
        verbose_name_plural = _('Association images')

    def __str__(self) -> str:
        if self.name:
            return _(f'Image association `{self.image}` ({self.name}) by {self.author}')
        return _(f'Image association `{self.image}` by {self.author}')


class QuoteAssociation(
    GetObjectModelMixin,
    WordsCountMixin,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    text = models.CharField(
        _('Quote text'),
        max_length=LengthLimits.MAX_QUOTE_TEXT_LENGTH,
        blank=False,
        validators=(
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    quote_author = models.CharField(
        _('Quote author'),
        max_length=LengthLimits.MAX_QUOTE_AUTHOR_LENGTH,
        blank=True,
        validators=(
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    get_object_by_fields = ('text',)

    class Meta:
        ordering = ('-created', '-modified')
        get_latest_by = ('created', 'modified')
        verbose_name = _('Association quote')
        verbose_name_plural = _('Association quotes')

    def __str__(self) -> str:
        if self.quote_author:
            return _(
                f'Quote association `{self.text}` ({self.quote_author}) by {self.author}'
            )
        return _(f'Quote association `{self.text}` by {self.author}')


class Collection(
    GetObjectBySlugModelMixin,
    WordsCountMixin,
    SlugModel,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(
        _('Collection title'),
        max_length=LengthLimits.MAX_COLLECTION_NAME_LENGTH,
        validators=(
            MinLengthValidator(LengthLimits.MIN_COLLECTION_NAME_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    description = models.CharField(
        _('Description'),
        max_length=LengthLimits.MAX_COLLECTION_DESCRIPTION_LENGTH,
        blank=True,
    )
    words = models.ManyToManyField(
        'Word',
        through='WordsInCollections',
        related_name='collections',
        verbose_name=_('Word in collection'),
        blank=True,
    )

    slugify_fields = ('title', ('author', 'username'))

    class Meta:
        verbose_name = _('Collection')
        verbose_name_plural = _('Collections')
        ordering = ('-created', '-modified', '-id')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(
                Lower('title'), 'author', name='unique_user_collection'
            )
        ]

    def __str__(self) -> str:
        return _(f'{self.title}')


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
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    forms_group = models.ForeignKey(
        FormsGroup,
        verbose_name=_('Forms group'),
        null=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s',
    )

    get_object_by_fields = ('word', 'forms_group')

    class Meta:
        verbose_name = _('Words forms group')
        verbose_name_plural = _('Words forms group')
        ordering = ('-created',)
        get_latest_by = ('created',)
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


class WordTranslations(GetObjectModelMixin, WordRelatedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    translation = models.ForeignKey(
        'WordTranslation',
        verbose_name=_('Translation'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    get_object_by_fields = ('word', 'translation')

    class Meta:
        verbose_name = _('Word translation')
        verbose_name_plural = _('Word translations')
        ordering = ('-created',)
        get_latest_by = ('created',)
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


class WordDefinitions(GetObjectModelMixin, WordRelatedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    definition = models.ForeignKey(
        'Definition',
        verbose_name=_('Definition'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    get_object_by_fields = ('word', 'definition')

    class Meta:
        verbose_name = _('Word definition')
        verbose_name_plural = _('Word definitions')
        ordering = ('-created',)
        get_latest_by = ('created',)
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


class WordUsageExamples(GetObjectModelMixin, WordRelatedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    example = models.ForeignKey(
        'UsageExample',
        verbose_name=_('Usage example'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    get_object_by_fields = ('word', 'example')

    class Meta:
        verbose_name = _('Word usage example')
        verbose_name_plural = _('Word usage examples')
        ordering = ('-created',)
        get_latest_by = ('created',)
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


class WordImageAssociations(GetObjectModelMixin, WordRelatedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    image = models.ForeignKey(
        'ImageAssociation',
        verbose_name=_('Image association'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    get_object_by_fields = ('word', 'image')

    class Meta:
        verbose_name = _('Word image')
        verbose_name_plural = _('Words images')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [
            models.UniqueConstraint(fields=['word', 'image'], name='unique_word_image')
        ]

    def __str__(self) -> str:
        return _(
            f'Image `{self.image}` was added to word `{self.word}` '
            f'({self.word.language.name}) as association at {self.created:%Y-%m-%d}'
        )


class WordQuoteAssociations(GetObjectModelMixin, WordRelatedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    quote = models.ForeignKey(
        'QuoteAssociation',
        verbose_name=_('Quote association'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    get_object_by_fields = ('word', 'quote')

    class Meta:
        verbose_name = _('Word quote')
        verbose_name_plural = _('Words quotes')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [
            models.UniqueConstraint(fields=['word', 'quote'], name='unique_word_quote')
        ]

    def __str__(self) -> str:
        return _(
            f'Quote `{self.quote}` was added to word `{self.word}` '
            f'({self.word.language.name}) as association at {self.created:%Y-%m-%d}'
        )


class WordsInCollections(GetObjectModelMixin, WordRelatedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    collection = models.ForeignKey(
        'Collection',
        verbose_name=_('Collection'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    get_object_by_fields = ('word', 'collection')

    class Meta:
        verbose_name = _('Words in collections')
        verbose_name_plural = _('Words in collections')
        ordering = ('-created',)
        get_latest_by = ('created',)
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


class WordSelfRelatedModel(GetObjectModelMixin, CreatedModel):
    to_word = models.ForeignKey(
        Word, related_name='%(class)s_to_words', on_delete=models.CASCADE
    )
    from_word = models.ForeignKey(
        Word, related_name='%(class)s_from_words', on_delete=models.CASCADE
    )

    get_object_by_fields = ('to_word', 'from_word')

    class Meta:
        abstract = True

    def get_classname(self):
        return self.__class__.__name__

    def __str__(self) -> str:
        classname = self.get_classname().lower()
        return '`{from_word}` is {classname} for `{to_word}`'.format(
            from_word=self.from_word, classname=classname, to_word=self.to_word
        )


class WordSelfRelatedWithNoteModel(WordSelfRelatedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    note = models.CharField(
        max_length=512,
        verbose_name=_('Note'),
        help_text=_('Note for %(class)ss'),
        blank=True,
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        if self.note:
            classname = self.get_classname().lower()
            return (
                '`{from_word}` is {classname} for `{to_word}`' '(note: {note})'
            ).format(
                from_word=self.from_word,
                to_word=self.to_word,
                note=self.note,
                classname=classname,
            )
        return super().__str__()


class Synonym(WordSelfRelatedWithNoteModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        verbose_name = _('Synonyms')
        verbose_name_plural = _('Synonyms')
        ordering = ('-from_word__created', '-created')
        get_latest_by = ('created',)
        constraints = [
            models.CheckConstraint(
                check=~models.Q(to_word=models.F('from_word')),
                name='synonym_not_same_word',
            ),
            models.UniqueConstraint(
                fields=['from_word', 'to_word'], name='unique_synonyms_pair'
            ),
        ]


class Antonym(WordSelfRelatedWithNoteModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        verbose_name = _('Antonym')
        verbose_name_plural = _('Antonyms')
        ordering = ('-from_word__created', '-created')
        get_latest_by = ('created',)
        constraints = [
            models.CheckConstraint(
                check=~models.Q(to_word=models.F('from_word')),
                name='antonym_not_same_word',
            ),
            models.UniqueConstraint(
                fields=['from_word', 'to_word'], name='unique_antonyms_pair'
            ),
        ]


class Form(WordSelfRelatedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        verbose_name = _('Form')
        verbose_name_plural = _('Forms')
        ordering = ('-from_word__created', '-created')
        get_latest_by = ('created',)
        constraints = [
            models.CheckConstraint(
                check=~models.Q(to_word=models.F('from_word')),
                name='form_not_same_word',
            ),
            models.UniqueConstraint(
                fields=['from_word', 'to_word'], name='unique_forms_pair'
            ),
        ]


class Similar(WordSelfRelatedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        verbose_name = _('Similar')
        verbose_name_plural = _('Similars')
        ordering = ('-from_word__created', '-created')
        get_latest_by = ('created',)
        constraints = [
            models.CheckConstraint(
                check=~models.Q(to_word=models.F('from_word')),
                name='similar_not_same_word',
            ),
            models.UniqueConstraint(
                fields=['from_word', 'to_word'], name='unique_similars_pair'
            ),
        ]


class Note(
    GetObjectBySlugModelMixin,
    SlugModel,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    word = models.ForeignKey(
        'Word',
        verbose_name=_('Word'),
        on_delete=models.CASCADE,
        related_name='notes',
        null=False,
    )
    text = models.CharField(
        _('Note text'), max_length=LengthLimits.MAX_NOTE_LENGTH, blank=False
    )

    slugify_fields = ('text', ('word', 'text'))

    class Meta:
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')
        ordering = ('-created', '-id')
        get_latest_by = ('created',)

    def __str__(self) -> str:
        return _(f'Note to the word `{self.word}`: {self.text} ')


class FavoriteWord(GetObjectModelMixin, UserRelatedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    word = models.ForeignKey(
        'Word',
        verbose_name=_('Word'),
        on_delete=models.CASCADE,
        related_name='favorite_for',
    )

    get_object_by_fields = ('word', 'user')

    class Meta:
        verbose_name = _('Favorite word')
        verbose_name_plural = _('Favorite words')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'user'], name='unique_user_favorite_word'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'The word `{self.word}` was added to favorites by '
            f'{self.user} at {self.created:%Y-%m-%d}'
        )


class FavoriteCollection(GetObjectModelMixin, UserRelatedModel):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    collection = models.ForeignKey(
        'Collection',
        verbose_name=_('Collection'),
        on_delete=models.CASCADE,
        related_name='favorite_for',
    )

    get_object_by_fields = ('collection', 'user')

    class Meta:
        verbose_name = _('Favorite collection')
        verbose_name_plural = _('Favorite collections')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [
            models.UniqueConstraint(
                fields=['collection', 'user'], name='unique_user_favorite_collection'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'The collection `{self.collection}` was added to favorites by '
            f'{self.user} at {self.created:%Y-%m-%d}'
        )


@receiver(pre_save, sender=Word)
@receiver(pre_save, sender=Collection)
@receiver(pre_save, sender=Type)
@receiver(pre_save, sender=FormsGroup)
@receiver(pre_save, sender=WordTranslation)
@receiver(pre_save, sender=Definition)
@receiver(pre_save, sender=UsageExample)
@receiver(pre_save, sender=Note)
def fill_slug(sender, instance, *args, **kwargs):
    return slug_filler(sender, instance, *args, **kwargs)


@receiver(post_delete, sender=Word)
def clear_extra_objects(sender, *args, **kwargs):
    """
    Delete word related objects if related to no words.
    (Удалить связанные объекты, если они больше не используются.)
    """
    WordTranslation.objects.filter(words__isnull=True).delete()
    UsageExample.objects.filter(words__isnull=True).delete()
    Definition.objects.filter(words__isnull=True).delete()
    Tag.objects.filter(words__isnull=True).delete()
    FormsGroup.objects.filter(words__isnull=True).delete()
    ImageAssociation.objects.filter(words__isnull=True).delete()
    QuoteAssociation.objects.filter(words__isnull=True).delete()
