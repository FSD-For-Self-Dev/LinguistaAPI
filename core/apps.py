''' Core app config '''

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'core'
    verbose_name = _('Core')
