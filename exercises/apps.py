''' Exercises app config '''

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ExercisesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exercises'
    verbose_name = _('Exercises')
