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
    WordsCountMixin,
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
        'en': 3,
        'ru': 2,
        'fr': 2,
        'de': 2,
        'it': 2,
        'ja': 2,
        'ko': 2,
        'es': 2,
        'tr': 1,
        'ar': 1,
        'nl': 1,
        'ro': 1,
    }
    LEARN_AVAILABLE = {
        'en': True,
        'ru': True,
        'fr': True,
        'de': True,
        'it': True,
        'es': True,
    }
    INTERFACE_AVAILABLE = {
        'en': True,
        'ru': True,
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
        help_text=_('2 character language code without country'),
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

    def __str__(self) -> str:
        return f'{self.name} ({self.name_local})'


def language_images_path(instance, filename) -> str:
    return f'languages/images/{instance.language.name}/{filename}'


class LanguageCoverImage(CreatedModel, ModifiedModel):
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
        return super().save(*args, **kwargs)


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

    slugify_fields = ('user', ('language', 'name'))

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

    slugify_fields = ('user', ('language', 'name'))

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
