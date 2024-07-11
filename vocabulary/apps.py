"""Vocabulary app config."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VocabularyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vocabulary'
    verbose_name = _('Vocabulary')
