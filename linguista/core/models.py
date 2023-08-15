''' Core models '''

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CreatedModel(models.Model):
    '''
    Abstract base class to add date created field
    '''

    created = models.DateTimeField(
        _('Date created'),
        editable=False,
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        abstract = True


class ModifiedModel(models.Model):
    '''
    Abstract base class to add date modified field
    '''

    modified = models.DateTimeField(
        _('Date modified'),
        blank=True,
        null=True
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        self.modified = timezone.now()
        return super().save(*args, **kwargs)


class Language(models.Model):
    '''
    List of languages by iso code (2 letter only because country code
    is not needed)
    This should be popluated by getting data from django.conf.locale.LANG_INFO
    '''

    name = models.CharField(
        _('Language name'),
        max_length=256,
        null=False,
        blank=False
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
        max_length=2,
        null=False,
        blank=False,
        unique=True,
        help_text=_('2 character language code without country')
    )
    sorting = models.PositiveIntegerField(
        _('Sorting order'),
        blank=False,
        null=False,
        default=0,
        help_text=_('increase to show at top of the list')
    )

    def __str__(self):
        return '%s (%s)' % (self.name, self.name_local)

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')
        ordering = ('-sorting', 'name', 'isocode')
