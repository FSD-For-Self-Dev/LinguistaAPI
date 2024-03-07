"""Модели приложения vocabulary."""

from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator, RegexValidator
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext as _

from core.models import (
    AuthorModel,
    CreatedModel,
    ModifiedModel,
    UserRelatedModel,
)
from languages.models import Language

from .constants import (
    LengthLimits,
    REGEX_TEXT_MASK_DETAIL,
    REGEX_TEXT_MASK,
    REGEX_HEXCOLOR_MASK,
    REGEX_HEXCOLOR_MASK_DETAIL,
)
from .utils import slugify_text_author_fields, slugify_text_word_fields

User = get_user_model()


class SlugModel(models.Model):
    slug = models.SlugField(_('Slug'), unique=True, blank=False, null=False)

    slugify_func = slugify_text_author_fields
    get_slug_by_fields = ('text', 'author')

    class Meta:
        abstract = True

    @classmethod
    def check_class_attrs(cls):
        assert hasattr(cls, 'slugify_func') and hasattr(cls, 'get_slug_by_fields'), (
            'Set `slugify_func`, `get_slug_by_fields` class attributes to use '
            'SlugModel.'
        )

    @classmethod
    def get_slug(cls, *args, **kwargs):
        cls.check_class_attrs()
        _slug_fields = []
        for field in cls.get_slug_by_fields:
            try:
                value = kwargs.get(field)
                if not value:
                    return None
                _slug_fields.append(value)
            except KeyError:
                raise AssertionError(
                    f'Can not get slug from data. Make sure {field} are passed in '
                    'data.'
                )
        return cls.slugify_func(*_slug_fields)

    @classmethod
    def get_object(cls, data):
        slug = cls.get_slug(**data)
        try:
            return cls.objects.get(slug=slug)
        except ObjectDoesNotExist:
            return None

    def save(self, *args, **kwargs):
        self.check_class_attrs()
        slugify_data = {
            field: self.__getattribute__(field) for field in self.get_slug_by_fields
        }
        self.slug = self.get_slug(**slugify_data)
        return super().save(*args, **kwargs)


class GetObjectModelMixin:
    get_object_by_fields = ('field',)

    @classmethod
    def check_class_attrs(cls):
        assert hasattr(
            cls, 'get_object_by_fields'
        ), 'Set `get_object_by_fields` class attributes to use GetObjectModelMixin.'

    @classmethod
    def get_object(cls, data):
        cls.check_class_attrs()
        for field in cls.get_object_by_fields:
            assert (
                field in data
            ), f'Can not get object from data. Make sure {field} are passed in data.'
        try:
            return cls.objects.get(**data)
        except ObjectDoesNotExist:
            return None


class Tag(GetObjectModelMixin, AuthorModel, CreatedModel, ModifiedModel):
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
        ordering = ['-created', '-modified']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')

    def __str__(self) -> str:
        return f'{self.name} (by {self.author})'


class Collection(CreatedModel, ModifiedModel, AuthorModel, SlugModel):
    title = models.CharField(
        _('Collection title'),
        max_length=LengthLimits.MAX_COLLECTION_NAME_LENGTH,
        validators=(
            MinLengthValidator(LengthLimits.MIN_COLLECTION_NAME_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )
    description = models.TextField(
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

    slugify_func = slugify_text_author_fields
    get_slug_by_fields = ('title', 'author')

    class Meta:
        ordering = ['-created', '-modified']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Collection')
        verbose_name_plural = _('Collections')
        constraints = [
            models.UniqueConstraint(
                Lower('title'), 'author', name='unique_user_collection'
            )
        ]

    def __str__(self) -> str:
        return _(f'{self.title}')

    def words_count(self) -> int:
        return self.words.count()


class Type(CreatedModel, ModifiedModel, AuthorModel, SlugModel):
    name = models.CharField(
        _('Type name'),
        max_length=64,
        unique=True,
        validators=(
            MinLengthValidator(1),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    slugify_func = slugify_text_author_fields
    get_slug_by_fields = ('name', 'author')

    class Meta:
        ordering = ['-created', '-modified']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Type')
        verbose_name_plural = _('Types')

    def __str__(self) -> str:
        return f'{self.name}'

    @property
    def words_count(self):
        return self.words.count()


class Word(CreatedModel, ModifiedModel, AuthorModel, SlugModel):
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
        max_length=LengthLimits.MAX_WORD_LENGTH,
        validators=(
            MinLengthValidator(LengthLimits.MIN_WORD_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
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
        related_name='example_for',
        verbose_name=_('Usage example'),
        blank=True,
    )

    slugify_func = slugify_text_author_fields
    get_slug_by_fields = ('text', 'author')

    class Meta:
        ordering = ['-created', '-modified']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Word or phrase')
        verbose_name_plural = _('Words and phrases')
        constraints = [
            models.UniqueConstraint('text', 'author', name='unique_words_in_user_voc')
        ]

    def __str__(self) -> str:
        return f'{self.text} (by {self.author})'


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
    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Synonyms')
        verbose_name_plural = _('Synonyms')
        constraints = [
            models.CheckConstraint(
                check=~models.Q(to_word=models.F('from_word')),
                name='synonym_not_same_word',
            ),  # need tests
            models.UniqueConstraint(
                fields=['from_word', 'to_word'], name='unique_synonyms_pair'
            ),
        ]


class Antonym(WordSelfRelatedWithNoteModel):
    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Antonym')
        verbose_name_plural = _('Antonyms')
        constraints = [
            models.CheckConstraint(
                check=~models.Q(to_word=models.F('from_word')),
                name='antonym_not_same_word',
            ),
            models.UniqueConstraint(
                fields=['from_word', 'to_word'], name='unique_antonyms_pair'
            ),
        ]


class FormsGroup(AuthorModel, CreatedModel, ModifiedModel, SlugModel):
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
    words = models.ManyToManyField(
        'Word',
        through='WordsFormGroups',
        related_name='forms_groups',
        verbose_name=_('Words in forms group'),
        blank=True,
    )

    slugify_func = slugify_text_author_fields
    get_slug_by_fields = ('name', 'author')

    class Meta:
        ordering = ['-created', '-modified']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Forms group')
        verbose_name_plural = _('Forms groups')
        ordering = ('-created', 'name')
        constraints = [
            models.UniqueConstraint(Lower('name'), 'author', name='unique_group_name')
        ]

    def __str__(self):
        return f'{self.name}'

    def save(self, *args, **kwargs):
        self.name = self.name.capitalize()
        super(FormsGroup, self).save(*args, **kwargs)


class Form(WordSelfRelatedModel):
    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Form')
        verbose_name_plural = _('Forms')
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
    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Similar')
        verbose_name_plural = _('Similars')
        constraints = [
            models.CheckConstraint(
                check=~models.Q(to_word=models.F('from_word')),
                name='similar_not_same_word',
            ),
            models.UniqueConstraint(
                fields=['from_word', 'to_word'], name='unique_similars_pair'
            ),
        ]


class WordTranslation(CreatedModel, ModifiedModel, AuthorModel, SlugModel):
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
        related_name='words_translations',
        default=Language.get_default_pk,
    )

    slugify_func = slugify_text_author_fields
    get_slug_by_fields = ('text', 'author')

    class Meta:
        ordering = ['-created', '-modified']
        get_latest_by = ['created', 'modified']
        verbose_name = _('Translation')
        verbose_name_plural = _('Translations')
        constraints = [
            models.UniqueConstraint(
                Lower('text'), 'author', name='unique_word_translation_in_user_voc'
            )
        ]

    def __str__(self) -> str:
        return f'{self.text} ({self.language})'


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

    get_object_by_fields = ('word', 'forms_group')

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


class WordsInCollections(GetObjectModelMixin, WordRelatedModel):
    collection = models.ForeignKey(
        'Collection',
        verbose_name=_('Collection'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    get_object_by_fields = ('word', 'collection')

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


class WordTranslations(GetObjectModelMixin, WordRelatedModel):
    translation = models.ForeignKey(
        'WordTranslation',
        verbose_name=_('Translation'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    get_object_by_fields = ('word', 'translation')

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


class Definition(CreatedModel, ModifiedModel, AuthorModel, SlugModel):
    text = models.CharField(
        _('Definition'),
        max_length=LengthLimits.MAX_DEFINITION_LENGTH,
        help_text=_('A definition of a word or phrase'),
        validators=(
            MinLengthValidator(LengthLimits.MIN_DEFINITION_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
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

    slugify_func = slugify_text_author_fields
    get_slug_by_fields = ('text', 'author')

    class Meta:
        ordering = ['-created', '-modified']
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


class WordDefinitions(GetObjectModelMixin, WordRelatedModel):
    definition = models.ForeignKey(
        'Definition',
        verbose_name=_('Definition'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    get_object_by_fields = ('word', 'definition')

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


class UsageExample(CreatedModel, ModifiedModel, AuthorModel, SlugModel):
    text = models.CharField(
        _('Usage example'),
        max_length=LengthLimits.MAX_EXAMPLE_LENGTH,
        help_text=_('An usage example of a word or phrase'),
        validators=(
            MinLengthValidator(LengthLimits.MIN_EXAMPLE_LENGTH),
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
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

    slugify_func = slugify_text_author_fields
    get_slug_by_fields = ('text', 'author')

    class Meta:
        ordering = ['-created', '-modified']
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


class WordUsageExamples(GetObjectModelMixin, WordRelatedModel):
    example = models.ForeignKey(
        'UsageExample',
        verbose_name=_('Usage example'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    get_object_by_fields = ('word', 'example')

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


class Note(CreatedModel, ModifiedModel, AuthorModel, SlugModel):
    word = models.ForeignKey(
        'Word',
        verbose_name=_('Word'),
        on_delete=models.CASCADE,
        related_name='notes',
        null=True,
    )
    text = models.CharField(
        _('Note text'), max_length=LengthLimits.MAX_NOTE_LENGTH, blank=False
    )

    slugify_func = slugify_text_word_fields
    get_slug_by_fields = ('text', 'word')

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')
        constraints = [
            models.UniqueConstraint(fields=['word', 'text'], name='unique_word_note')
        ]

    def __str__(self) -> str:
        return _(f'Note to the word `{self.word}`: {self.text} ')


class ImageAssociation(
    CreatedModel, ModifiedModel
):  # set ManytoMany relation with word; get_object
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
        max_length=LengthLimits.MAX_IMAGE_NAME_LENGTH,
        blank=True,
        validators=(
            RegexValidator(regex=REGEX_TEXT_MASK, message=REGEX_TEXT_MASK_DETAIL),
        ),
    )

    class Meta:
        verbose_name = _('Association image')
        verbose_name_plural = _('Association images')

    def __str__(self) -> str:
        if self.name:
            return _(f'Image `{self.name}` for `{self.word}`')
        return _(f'Image for `{self.word}`')


class FavoriteWord(GetObjectModelMixin, UserRelatedModel):
    word = models.ForeignKey(
        'Word',
        verbose_name=_('Word'),
        on_delete=models.CASCADE,
        related_name='favorite_for',
    )

    get_object_by_fields = ('word', 'user')

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Favorite word')
        verbose_name_plural = _('Favorite words')
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
    collection = models.ForeignKey(
        'Collection',
        verbose_name=_('Collection'),
        on_delete=models.CASCADE,
        related_name='favorite_for',
    )

    get_object_by_fields = ('collection', 'user')

    class Meta:
        ordering = ['-created']
        get_latest_by = ['created']
        verbose_name = _('Favorite collection')
        verbose_name_plural = _('Favorite collections')
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
