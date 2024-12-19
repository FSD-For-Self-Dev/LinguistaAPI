"""Languages app models."""

import uuid
import logging

from django.db import models
from django.utils.translation import gettext as _
from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.core.models import (
    CreatedModel,
    ModifiedModel,
    SlugModel,
    GetObjectBySlugModelMixin,
    GetObjectModelMixin,
    WordsCountMixin,
    AuthorModel,
)
from config.settings import AUTH_USER_MODEL
from utils.fillers import slug_filler
from utils.images import compress

logger = logging.getLogger(__name__)


class Language(WordsCountMixin, models.Model):
    """
    List of languages by iso code (2 letter only because country code
    is not needed)
    This should be popluated by getting data from django.conf.locale.LANG_INFO
    """

    LANGS_SORTING_VALS = {
        'en-gb': 3,
        'en-us': 3,
        'ru-ru': 2,
        'fr-fr': 2,
        'de-de': 2,
        'it-it': 2,
        'ja-jp': 2,
        'ko-kr': 2,
        'zh-cn': 2,
        'es-es': 2,
        'tr-tr': 1,
        'ar-ae': 1,
        'nl-nl': 1,
        'ro-ro': 1,
        'hy-am': 1,
        'be-by': 1,
        'bg-bg': 1,
        'el-gr': 1,
        'ka-ge': 1,
        'kk-kz': 1,
        'id-id': 1,
        'da-dk': 1,
        'ga-ie': 1,
        'zh-tw': 1,
        'pl-pl': 1,
        'pt-pt': 1,
        'th-th': 1,
        'hi-in': 1,
        'sw-ke': 1,
        'sv-se': 1,
        'bn-bd': 1,
    }
    LEARN_AVAILABLE = {
        'en-gb': True,
        'en-us': True,
        'ru-ru': True,
        'fr-fr': True,
        'de-de': True,
        'it-it': True,
        'es-es': True,
    }
    INTERFACE_AVAILABLE = {
        'en-gb': True,
        'en-us': True,
        'ru-ru': True,
    }

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(
        _('Language name'),
        max_length=256,
        null=False,
        blank=False,
    )
    name_local = models.CharField(
        _('Language name (in that language)'),
        max_length=256,
        null=False,
        blank=True,
        default='',
    )
    isocode = models.CharField(
        _('ISO 639-1 Language code'),
        max_length=8,
        null=False,
        blank=False,
        unique=True,
        help_text=_('2 or 3 character language code with 2 character country code'),
    )
    country = models.CharField(
        _('Country name'),
        max_length=256,
        null=False,
        blank=True,
    )
    sorting = models.PositiveIntegerField(
        _('Sorting order'),
        blank=False,
        null=False,
        default=0,
        help_text=_('Increase to show at top of the list'),
    )
    learning_available = models.BooleanField(
        _('Is the language available for user to add to learning ones'),
        default=False,
    )
    interface_available = models.BooleanField(
        _('Is the language available as interface language'),
        default=False,
    )
    flag_icon = models.ImageField(
        _('Language flag icon'),
        upload_to='languages/flag_icons/',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')
        db_table_comment = _('Languages')
        ordering = ('-sorting', 'name', 'isocode')
        get_latest_by = ('name',)

    def __str__(self) -> str:
        return f'{self.name} ({self.country})'


def language_images_path(instance, filename) -> str:
    return f'languages/images/{instance.language.isocode}/{filename}'


class LanguageCoverImage(
    GetObjectModelMixin,
    CreatedModel,
    ModifiedModel,
    AuthorModel,
):
    """Images available to be set as cover for the learning language."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(
        _('Language image'),
        upload_to=language_images_path,
        blank=False,
        null=False,
    )

    get_object_by_fields = ('id',)

    class Meta:
        verbose_name = _('Language image')
        verbose_name_plural = _('Languages images')
        db_table_comment = _(
            'Images available to be set as cover for the learning language'
        )
        ordering = ('-created', '-modified')

    def __str__(self) -> str:
        return f'Image for {self.language.name} language: {self.image.url}'

    def save(self, *args, **kwargs) -> None:
        """Compress the image file before saving it."""
        if self.image:
            self.image = compress(self.image)
        return super(LanguageCoverImage, self).save(*args, **kwargs)

    def image_size(self) -> int:
        """Returns image size."""
        return f'{round(self.image.size / 1024, 3)} KB'


class UserLearningLanguage(
    GetObjectBySlugModelMixin,
    SlugModel,
    CreatedModel,
    ModifiedModel,
):
    """Users learning languages."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.CASCADE,
        related_name='learning_by_detail',
    )
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='learning_languages_detail',
    )
    cover = models.ForeignKey(
        LanguageCoverImage,
        verbose_name=_('Learning language cover image'),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='covers',
    )
    level = models.CharField(
        _('Level of knowledge'),
        max_length=256,
        null=True,
        blank=True,
        default='',
    )

    slugify_fields = ('user', ('language', 'isocode'))

    class Meta:
        verbose_name = _('User learning language')
        verbose_name_plural = _('User learning languages')
        db_table_comment = _('Users learning languages')
        ordering = ('-created', '-modified')
        constraints = [
            models.UniqueConstraint(
                'language', 'user', name='unique_user_learning_language'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} studies {self.language}'


class UserNativeLanguage(SlugModel, CreatedModel):
    """Users native languages."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.CASCADE,
        related_name='native_for_detail',
    )
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='native_languages_detail',
    )

    slugify_fields = ('user', ('language', 'isocode'))

    class Meta:
        verbose_name = _('User native language')
        verbose_name_plural = _('User native languages')
        db_table_comment = _('Users native languages')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [
            models.UniqueConstraint(
                'language', 'user', name='unique_user_native_language'
            )
        ]

    def __str__(self) -> str:
        return f'{self.language} is native language for {self.user}'


@receiver(pre_save, sender=UserLearningLanguage)
@receiver(pre_save, sender=UserNativeLanguage)
def fill_slug(sender, instance, *args, **kwargs) -> None:
    """Fill slug field before save instance."""
    slug = slug_filler(sender, instance, *args, **kwargs)
    logger.debug(f'Instance {instance} slug filled with value: {slug}')
