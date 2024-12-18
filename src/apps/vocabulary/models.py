"""Vocabulary app models."""

import uuid
import logging

from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models.functions import Lower
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext as _

from apps.core.models import (
    GetObjectBySlugModelMixin,
    GetObjectModelMixin,
    WordsCountMixin,
    CreatedModel,
    ModifiedModel,
    SlugModel,
    UserRelatedModel,
    AuthorModel,
    ActivityStatusModel,
)
from apps.core.constants import (
    REGEX_TEXT_MASK_DETAIL,
    REGEX_TEXT_MASK,
    REGEX_HEXCOLOR_MASK,
    REGEX_HEXCOLOR_MASK_DETAIL,
    REGEX_COLLECTIONS_TITLE_MASK,
    REGEX_COLLECTIONS_TITLE_MASK_DETAIL,
    REGEX_FORM_GROUP_NAME_MASK,
    REGEX_FORM_GROUP_NAME_MASK_DETAIL,
    REGEX_DEFINITIONS_TEXT_MASK,
    REGEX_DEFINITIONS_TEXT_MASK_DETAIL,
    REGEX_EXAMPLES_TEXT_MASK,
    REGEX_EXAMPLES_TEXT_MASK_DETAIL,
)
from apps.core.validators import CustomRegexValidator
from utils.fillers import slug_filler
from utils.images import compress

from .constants import (
    VocabularyLengthLimits,
)

logger = logging.getLogger(__name__)


class Word(
    GetObjectBySlugModelMixin,
    SlugModel,
    AuthorModel,
    CreatedModel,
    ModifiedModel,
    ActivityStatusModel,
):
    """Users words and phrases."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    language = models.ForeignKey(
        'languages.Language',
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
            CustomRegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    activity_status = models.CharField(
        _('Activity status'),
        max_length=8,
        choices=ActivityStatusModel.ACTIVITY,
        blank=False,
        default=ActivityStatusModel.INACTIVE,
    )
    is_problematic = models.BooleanField(
        _('Is the word problematic for you'),
        default=False,
    )
    note = models.CharField(
        _('Note text'),
        max_length=VocabularyLengthLimits.MAX_NOTE_LENGTH,
        blank=True,
    )
    types = models.ManyToManyField(
        'WordType',
        verbose_name=_('WordType'),
        related_name='words',
        blank=True,
    )
    tags = models.ManyToManyField(
        'WordTag',
        verbose_name=_('Word tags'),
        related_name='words',
        blank=True,
    )
    form_groups = models.ManyToManyField(
        'FormGroup',
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
    image_associations = models.ManyToManyField(
        'ImageAssociation',
        through='WordImageAssociations',
        related_name='words',
        verbose_name=_('Image association'),
        blank=True,
    )
    quote_associations = models.ManyToManyField(
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

    slugify_fields = ('text', ('author', 'username'), ('language', 'isocode'))

    class Meta:
        verbose_name = _('Word or phrase')
        verbose_name_plural = _('Words and phrases')
        db_table_comment = _('Users words and phrases')
        ordering = ('-created', '-modified', '-id')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(
                'text', 'author', 'language', name='unique_words_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        return f'{self.text} (by {self.author})'


class WordType(
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
        _('Word type name'),
        max_length=64,
        unique=True,
        validators=(
            MinLengthValidator(1),
            CustomRegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    slugify_fields = ('name_en',)

    class Meta:
        verbose_name = _('Word type')
        verbose_name_plural = _('Word types')
        db_table_comment = _('Word or phrase types')
        ordering = ('-created', '-modified', '-id')
        get_latest_by = ('created', 'modified')

    def __str__(self) -> str:
        return f'{self.name}'


class WordTag(
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
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_TAG_LENGTH),
            CustomRegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    get_object_by_fields = ('name', 'author')

    class Meta:
        verbose_name = _('Word tag')
        verbose_name_plural = _('Word tags')
        db_table_comment = _('Word or phrase tags')
        ordering = ('-created', '-modified')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(Lower('name'), 'author', name='unique_tag_name')
        ]

    def __str__(self) -> str:
        return f'{self.name} (by {self.author})'

    def save(self, *args, **kwargs) -> None:
        """Reduce name to lowercase before instance save."""
        self.name = self.name.lower()
        return super().save(*args, **kwargs)


class FormGroup(
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
            CustomRegexValidator(
                regex=REGEX_FORM_GROUP_NAME_MASK,
                message=REGEX_FORM_GROUP_NAME_MASK_DETAIL,
            ),
        ),
    )
    language = models.ForeignKey(
        'languages.Language',
        verbose_name=_('Language'),
        on_delete=models.SET_NULL,
        related_name='form_groups',
        null=True,
    )
    color = models.CharField(
        _('Group color'),
        max_length=7,
        blank=True,
        validators=(
            MinLengthValidator(7),
            CustomRegexValidator(
                regex=REGEX_HEXCOLOR_MASK, message=REGEX_HEXCOLOR_MASK_DETAIL
            ),
        ),
    )
    translation = models.CharField(
        _('Group name translation'),
        max_length=VocabularyLengthLimits.MAX_FORMSGROUP_TRANSLATION_LENGTH,
        blank=True,
        validators=(
            CustomRegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
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
        """Capitalizes name before instance save."""
        self.name = self.name.capitalize()
        super().save(*args, **kwargs)


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
            CustomRegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    language = models.ForeignKey(
        'languages.Language',
        verbose_name=_('Language'),
        on_delete=models.SET_NULL,
        related_name='word_translations',
        null=True,
    )

    slugify_fields = ('text', ('author', 'username'), ('language', 'name'))

    class Meta:
        verbose_name = _('Translation')
        verbose_name_plural = _('Translations')
        db_table_comment = _('Translations for words and phrases')
        ordering = ('-created', '-modified')
        get_latest_by = ('created', 'modified')
        constraints = [
            models.UniqueConstraint(
                Lower('text'),
                'author',
                'language',
                name='unique_word_translation_in_user_voc',
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
            CustomRegexValidator(
                regex=REGEX_DEFINITIONS_TEXT_MASK,
                message=REGEX_DEFINITIONS_TEXT_MASK_DETAIL,
            ),
        ),
    )
    language = models.ForeignKey(
        'languages.Language',
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
            CustomRegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
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

    OTHER = 'other'
    BOOK = 'book'
    FILM = 'film'
    SONG = 'song'
    QUOTE = 'quote'
    SOURCE_OPTIONS = [
        (OTHER, _('Other')),
        (BOOK, _('Book')),
        (FILM, _('Film')),
        (SONG, _('Song')),
        (QUOTE, _('Quote')),
    ]

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
            CustomRegexValidator(
                regex=REGEX_EXAMPLES_TEXT_MASK, message=REGEX_EXAMPLES_TEXT_MASK_DETAIL
            ),
        ),
    )
    language = models.ForeignKey(
        'languages.Language',
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
            CustomRegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    source = models.CharField(
        _('Example source type'),
        max_length=64,
        choices=SOURCE_OPTIONS,
        blank=False,
        default=OTHER,
    )
    source_url = models.CharField(
        _('Example source hotlink'),
        max_length=512,
        null=True,
        blank=True,
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


def image_associations_path(instance, filename) -> str:
    return f'vocabulary/associations/{instance.author.username}/{filename}'


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
        upload_to=image_associations_path,
        null=True,
        blank=True,
    )
    image_url = models.CharField(
        _('Image hotlink'),
        max_length=512,
        null=True,
        blank=True,
    )

    get_object_by_fields = ('id',)

    class Meta:
        verbose_name = _('Image-association')
        verbose_name_plural = _('Image-associations')
        db_table_comment = _('Image-associations for words and phrases')
        ordering = ('-created', '-modified')
        get_latest_by = ('created', 'modified')

    def __str__(self) -> str:
        return _(f'Image association by {self.author}')

    def save(self, *args, **kwargs) -> None:
        """Compress the image file before saving it."""
        if self.image:
            self.image = compress(self.image)
        return super(ImageAssociation, self).save(*args, **kwargs)

    def image_size(self) -> int:
        """Returns image size."""
        if self.image:
            return f'{round(self.image.size / 1024, 3)} KB'
        return None


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
            CustomRegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    quote_author = models.CharField(
        _('Quote author'),
        max_length=VocabularyLengthLimits.MAX_QUOTE_AUTHOR_LENGTH,
        blank=True,
        validators=(
            CustomRegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
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
        max_length=VocabularyLengthLimits.MAX_COLLECTION_TITLE_LENGTH,
        validators=(
            MinLengthValidator(VocabularyLengthLimits.MIN_COLLECTION_TITLE_LENGTH),
            CustomRegexValidator(
                regex=REGEX_COLLECTIONS_TITLE_MASK,
                message=REGEX_COLLECTIONS_TITLE_MASK_DETAIL,
            ),
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
        'FormGroup',
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
            f'`{self.word}` is translated as `{self.translation}` '
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
        return f'`{self.from_word}` is {classname} for `{self.to_word}`'


class WordSelfRelatedWithNoteModel(WordSelfRelatedModel):
    """Words related to other words intermediary abstract model with `note` field."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    note = models.CharField(
        max_length=VocabularyLengthLimits.MAX_NOTE_LENGTH,
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
                f'`{self.from_word}` is {classname} for `{self.to_word}` '
                '(note: {self.note})'
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


class FavoriteWord(GetObjectModelMixin, UserRelatedModel, CreatedModel):
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


class FavoriteCollection(GetObjectModelMixin, UserRelatedModel, CreatedModel):
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


class DefaultWordCards(UserRelatedModel, CreatedModel):
    """Default word cards type set by user."""

    STANDART = 'standart'
    SHORT = 'short'
    LONG = 'long'
    VIEW_OPTIONS = [
        (STANDART, _('Standart')),
        (SHORT, _('Short')),
        (LONG, _('Long')),
    ]

    cards_type = models.CharField(
        _('Word cards type'),
        max_length=8,
        choices=VIEW_OPTIONS,
        blank=False,
        default=STANDART,
    )

    class Meta:
        verbose_name = _('User default word cards type setting')
        verbose_name_plural = _('User default word cards type settings')
        db_table_comment = _('Default word cards type set by user')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [
            models.UniqueConstraint('user', name='unique_default_word_cards_setting')
        ]

    def __str__(self) -> str:
        return f'Default word cards type set by {self.user}: {self.cards_type}'


@receiver(pre_save, sender=Word)
@receiver(pre_save, sender=Collection)
@receiver(pre_save, sender=WordType)
@receiver(pre_save, sender=FormGroup)
@receiver(pre_save, sender=WordTranslation)
@receiver(pre_save, sender=Definition)
@receiver(pre_save, sender=UsageExample)
def fill_slug(sender, instance, *args, **kwargs) -> None:
    """Fill slug field before save instance."""
    slug = slug_filler(sender, instance, *args, **kwargs)
    logger.debug(f'Instance {instance} slug filled with value: {slug}')


@receiver(post_delete, sender=Word)
def clear_extra_objects(sender, *args, **kwargs) -> None:
    """Delete word related objects if they no longer relate to other words."""
    WordTranslation.objects.filter(words__isnull=True).delete()
    UsageExample.objects.filter(words__isnull=True).delete()
    Definition.objects.filter(words__isnull=True).delete()
    WordTag.objects.filter(words__isnull=True).delete()
    FormGroup.objects.filter(words__isnull=True).delete()
    ImageAssociation.objects.filter(words__isnull=True).delete()
    QuoteAssociation.objects.filter(words__isnull=True).delete()
