"""Vocabulary models."""

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
    VocabularyLengthLimits,
    REGEX_TEXT_MASK_DETAIL,
    REGEX_TEXT_MASK,
    REGEX_HEXCOLOR_MASK,
    REGEX_HEXCOLOR_MASK_DETAIL,
)

User = get_user_model()


class WordsCountMixin:
    """Custom model mixin to add `words_count` method"""

    def words_count(self) -> int:
        """
        Returns object related words amount.
        Related name of word objects must be `words`.
        """
        return self.words.count()


class UserRelatedModel(CreatedModel):
    """Abstract model to add `user` field for related user."""

    user = models.ForeignKey(
        User,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    class Meta:
        abstract = True


class AuthorModel(models.Model):
    """Abstract model to add `author` field for related user."""

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
    """Users words and phrases."""

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
        on_delete=models.SET_NULL,
        related_name='words',
        null=True,
    )
    text = models.CharField(
        _('Word or phrase'),
        blank=False,
        max_length=VocabularyLengthLimits.MAX_WORD_LENGTH,
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_WORD_LENGTH),
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
        db_table_comment = _('Users words and phrases')
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
    """Words and phrases types."""

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
        db_table_comment = _('Words and phrases types')
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
    """Words and phrases tags."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        _('Tag name'),
        max_length=VocabularyLengthLimits.MAX_TAG_LENGTH,
        unique=True,
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_TAG_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    get_object_by_fields = ('name', 'author')

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        db_table_comment = _('Words and phrases tags')
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
    """Groups of possible word forms in language."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        _('Group name'),
        max_length=VocabularyLengthLimits.MAX_FORMSGROUP_NAME_LENGTH,
        blank=False,
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_FORMSGROUP_NAME_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.SET_NULL,
        related_name='forms_groups',
        null=True,
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
        max_length=VocabularyLengthLimits.MAX_FORMSGROUP_NAME_LENGTH,
        blank=True,
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_FORMSGROUP_NAME_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    slugify_fields = ('name', ('author', 'username'))

    class Meta:
        verbose_name = _('Forms group')
        verbose_name_plural = _('Forms groups')
        db_table_comment = _('Groups of possible word forms in language')
        ordering = ('-created', '-modified', 'name')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(Lower('name'), 'author', name='unique_group_name')
        ]

    def __str__(self) -> str:
        return f'{self.name}'

    def save(self, *args, **kwargs) -> None:
        """Capitalizes name text before instance save."""
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
    """Users words and phrases translations."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    text = models.CharField(
        _('Translation'),
        max_length=VocabularyLengthLimits.MAX_TRANSLATION_LENGTH,
        help_text=_('A translation of a word or phrase'),
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_TRANSLATION_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.SET_NULL,
        related_name='word_translations',
        null=True,
    )

    slugify_fields = ('text', ('author', 'username'))

    class Meta:
        verbose_name = _('Translation')
        verbose_name_plural = _('Translations')
        db_table_comment = _('Translations for words and phrases')
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
    """Users words and phrases definitions."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    text = models.CharField(
        _('Definition'),
        max_length=VocabularyLengthLimits.MAX_DEFINITION_LENGTH,
        help_text=_('A definition of a word or phrase'),
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_DEFINITION_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.SET_NULL,
        related_name='definitions',
        null=True,
    )
    translation = models.CharField(
        _('A translation of the definition'),
        max_length=VocabularyLengthLimits.MAX_DEFINITION_LENGTH,
        blank=True,
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_DEFINITION_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    slugify_fields = ('text', ('author', 'username'))

    class Meta:
        verbose_name = _('Definition')
        verbose_name_plural = _('Definitions')
        db_table_comment = _('Definitions for words and phrases')
        ordering = ('-created', '-modified', '-id')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(
                Lower('text'), 'author', name='unique_definition_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        if self.translation:
            return f'{self.text} ({self.translation})'
        return self.text


class UsageExample(
    GetObjectBySlugModelMixin,
    WordsCountMixin,
    SlugModel,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    """Users words and phrases usage examples."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    text = models.CharField(
        _('Usage example'),
        max_length=VocabularyLengthLimits.MAX_EXAMPLE_LENGTH,
        help_text=_('An usage example of a word or phrase'),
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_EXAMPLE_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.SET_NULL,
        related_name='examples',
        null=True,
    )
    translation = models.CharField(
        _('A translation of the example'),
        max_length=VocabularyLengthLimits.MAX_EXAMPLE_LENGTH,
        blank=True,
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_EXAMPLE_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    slugify_fields = ('text', ('author', 'username'))

    class Meta:
        verbose_name = _('Usage example')
        verbose_name_plural = _('Usage examples')
        db_table_comment = _('Usage examples for words and phrases')
        ordering = ('-created', '-modified')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(
                Lower('text'), 'author', name='unique_word_usage_example_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        if self.translation:
            return f'{self.text} ({self.translation})'
        return self.text


class ImageAssociation(
    GetObjectModelMixin,
    WordsCountMixin,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    """Users words and phrases image-associations."""

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

    get_object_by_fields = ('image',)

    class Meta:
        verbose_name = _('Image-association')
        verbose_name_plural = _('Image-associations')
        db_table_comment = _('Image-associations for words and phrases')
        ordering = ('-created', '-modified')
        get_latest_by = ('created', 'modified')

    def __str__(self) -> str:
        return _(f'Image association `{self.image}` by {self.author}')


class QuoteAssociation(
    GetObjectModelMixin,
    WordsCountMixin,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    """Users words and phrases quote-associations."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    text = models.CharField(
        _('Quote text'),
        max_length=VocabularyLengthLimits.MAX_QUOTE_TEXT_LENGTH,
        blank=False,
        validators=(
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    quote_author = models.CharField(
        _('Quote author'),
        max_length=VocabularyLengthLimits.MAX_QUOTE_AUTHOR_LENGTH,
        blank=True,
        validators=(
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    get_object_by_fields = ('text',)

    class Meta:
        verbose_name = _('Quote-association')
        verbose_name_plural = _('Quote-associations')
        db_table_comment = _('Quote-associations for words and phrases')
        ordering = ('-created', '-modified')
        get_latest_by = ('created', 'modified')

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
    """Users words and phrases collections."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    title = models.CharField(
        _('Collection title'),
        max_length=VocabularyLengthLimits.MAX_COLLECTION_NAME_LENGTH,
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_COLLECTION_NAME_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    description = models.CharField(
        _('Description'),
        max_length=VocabularyLengthLimits.MAX_COLLECTION_DESCRIPTION_LENGTH,
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
        db_table_comment = _('Collections of words and phrases')
        ordering = ('-created', '-modified', '-id')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(
                Lower('title'), 'author', name='unique_user_collection'
            )
        ]

    def __str__(self) -> str:
        return self.title


class WordRelatedModel(CreatedModel):
    """Abstract model to add `word` field for related word."""

    word = models.ForeignKey(
        'Word',
        verbose_name=_('Word'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    class Meta:
        abstract = True


class WordsFormGroups(WordRelatedModel):
    """Words and form groups intermediary model."""

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
        verbose_name = _('Word form group (intermediary model)')
        verbose_name_plural = _('Words form groups (intermediary model)')
        db_table_comment = _('Intermediary model for words and form groups')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'forms_group'], name='unique_word_forms_group'
            )
        ]

    def __str__(self) -> str:
        return _(f'Word `{self.word}` is in `{self.forms_group}` form')


class WordTranslations(GetObjectModelMixin, WordRelatedModel):
    """Words and translations intermediary model."""

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
        verbose_name = _('Word translation (intermediary model)')
        verbose_name_plural = _('Word translations (intermediary model)')
        db_table_comment = _('Words and its translations intermediary model')
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
    """Words and definitions intermediary model."""

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
        verbose_name = _('Word definition (intermediary model)')
        verbose_name_plural = _('Word definitions (intermediary model)')
        db_table_comment = _('Words and definitions intermediary model')
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
    """Words and usage examples intermediary model."""

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
        verbose_name = _('Word usage example (intermediary model)')
        verbose_name_plural = _('Word usage examples (intermediary model)')
        db_table_comment = _('Words and usage examples intermediary model')
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
    """Words and image-associations intermediary model."""

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
        verbose_name = _('Word image-association (intermediary model)')
        verbose_name_plural = _('Words image-associations (intermediary model)')
        db_table_comment = _('Words and image-associations intermediary model')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [
            models.UniqueConstraint(fields=['word', 'image'], name='unique_word_image')
        ]

    def __str__(self) -> str:
        return _(
            f'Image `{self.image}` was added to word `{self.word}` associations at {self.created:%Y-%m-%d}'
        )


class WordQuoteAssociations(GetObjectModelMixin, WordRelatedModel):
    """Words and quote-associations intermediary model."""

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
        verbose_name = _('Word quote-association (intermediary model)')
        verbose_name_plural = _('Words quote-associations (intermediary model)')
        db_table_comment = _('Words and quote-associations intermediary model')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [
            models.UniqueConstraint(fields=['word', 'quote'], name='unique_word_quote')
        ]

    def __str__(self) -> str:
        return _(
            f'Quote `{self.quote}` was added to word `{self.word}` associations at {self.created:%Y-%m-%d}'
        )


class WordsInCollections(GetObjectModelMixin, WordRelatedModel):
    """Words and collections intermediary model."""

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
        verbose_name = _('Word in collection (intermediary model)')
        verbose_name_plural = _('Words in collections (intermediary model)')
        db_table_comment = _('Words and collections intermediary model')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'collection'], name='unique_word_in_collection'
            )
        ]

    def __str__(self) -> str:
        return _(
            f'Word `{self.word}` was added to collection `{self.collection}` at {self.created:%Y-%m-%d}'
        )


class WordSelfRelatedModel(GetObjectModelMixin, CreatedModel):
    """Words related to other words intermediary abstract model."""

    to_word = models.ForeignKey(
        Word,
        related_name='%(class)s_to_words',
        on_delete=models.CASCADE,
    )
    from_word = models.ForeignKey(
        Word,
        related_name='%(class)s_from_words',
        on_delete=models.CASCADE,
    )

    get_object_by_fields = ('to_word', 'from_word')

    class Meta:
        abstract = True

    def get_classname(self) -> str:
        return self.__class__.__name__

    def __str__(self) -> str:
        classname = self.get_classname().lower()
        return '`{from_word}` is {classname} for `{to_word}`'.format(
            from_word=self.from_word, classname=classname, to_word=self.to_word
        )


class WordSelfRelatedWithNoteModel(WordSelfRelatedModel):
    """Words related to other words intermediary abstract model with `note` field."""

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
    """Words synonyms."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        verbose_name = _('Synonyms')
        verbose_name_plural = _('Synonyms')
        db_table_comment = _('Words synonyms')
        ordering = ('-from_word__created', '-created')
        get_latest_by = ('created',)
        constraints = [
            models.CheckConstraint(
                check=~models.Q(to_word=models.F('from_word')),
                name='synonym_not_same_word',
            ),
        ]


class Antonym(WordSelfRelatedWithNoteModel):
    """Words antonyms."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        verbose_name = _('Antonym')
        verbose_name_plural = _('Antonyms')
        db_table_comment = _('Words antonyms')
        ordering = ('-from_word__created', '-created')
        get_latest_by = ('created',)
        constraints = [
            models.CheckConstraint(
                check=~models.Q(to_word=models.F('from_word')),
                name='antonym_not_same_word',
            ),
        ]


class Form(WordSelfRelatedModel):
    """Words forms."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        verbose_name = _('Form')
        verbose_name_plural = _('Forms')
        db_table_comment = _('Words forms')
        ordering = ('-from_word__created', '-created')
        get_latest_by = ('created',)
        constraints = [
            models.CheckConstraint(
                check=~models.Q(to_word=models.F('from_word')),
                name='form_not_same_word',
            ),
        ]


class Similar(WordSelfRelatedModel):
    """Similar words."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        verbose_name = _('Similar')
        verbose_name_plural = _('Similars')
        db_table_comment = _('Similar words')
        ordering = ('-from_word__created', '-created')
        get_latest_by = ('created',)
        constraints = [
            models.CheckConstraint(
                check=~models.Q(to_word=models.F('from_word')),
                name='similar_not_same_word',
            ),
        ]


class Note(
    GetObjectBySlugModelMixin,
    SlugModel,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
):
    """Word notes."""

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
        _('Note text'),
        max_length=VocabularyLengthLimits.MAX_NOTE_LENGTH,
        blank=False,
    )

    slugify_fields = ('text', ('word', 'text'))

    class Meta:
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')
        db_table_comment = _('Word notes')
        ordering = ('-created', '-id')
        get_latest_by = ('created',)

    def __str__(self) -> str:
        return _(f'Note to the word `{self.word}`: {self.text} ')


class FavoriteWord(GetObjectModelMixin, UserRelatedModel):
    """Users favorite words."""

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
        db_table_comment = _('Users favorite words')
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
    """Users favorite collections."""

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
        db_table_comment = _('Users favorite collections')
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
def fill_slug(sender, instance, *args, **kwargs) -> None:
    """Fill slug field before save instance."""
    return slug_filler(sender, instance, *args, **kwargs)


@receiver(post_delete, sender=Word)
def clear_extra_objects(sender, *args, **kwargs) -> None:
    """Delete word related objects if they no longer relate to other words."""
    WordTranslation.objects.filter(words__isnull=True).delete()
    UsageExample.objects.filter(words__isnull=True).delete()
    Definition.objects.filter(words__isnull=True).delete()
    Tag.objects.filter(words__isnull=True).delete()
    FormsGroup.objects.filter(words__isnull=True).delete()
    ImageAssociation.objects.filter(words__isnull=True).delete()
    QuoteAssociation.objects.filter(words__isnull=True).delete()
