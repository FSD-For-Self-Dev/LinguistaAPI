''' Languages models '''

from django.db import models
from django.utils.translation import gettext_lazy as _


class Language(models.Model):
    '''
    List of languages by iso code (2 letter only because country code
    is not needed)
    This should be popluated by getting data from django.conf.locale.LANG_INFO
    '''

    LANGS_SORTING_VALS = {
        "en": 3,
        "ru": 2,
        "fr": 2,
        "de": 2,
        "it": 2,
        "ja": 2,
        "ko": 2,
        "es": 2,
        "tr": 1,
        "ar": 1,
        "nl": 1,
        "ro": 1,
    }

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

    @classmethod
    def get_default_pk(cls):
        lang, created = cls.objects.get_or_create(
            isocode='en',
            defaults={
                'name': 'English',
                'name_local': 'English',
                'sorting': cls.LANGS_SORTING_VALS.get('en', 3)
            },
        )
        return lang.pk

    class Meta:
        verbose_name = _('Language')
        verbose_name_plural = _('Languages')
        ordering = ('-sorting', 'name', 'isocode')
