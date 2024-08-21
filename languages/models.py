"""Languages models."""

import uuid

from django.db import models
from django.utils.translation import gettext as _

from core.models import CreatedModel, ModifiedModel


class Language(models.Model):
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


class LanguageImage(CreatedModel, ModifiedModel):
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
        upload_to='languages/images/',
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
