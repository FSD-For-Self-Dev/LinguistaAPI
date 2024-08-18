"""Core constants."""

import os

from django.utils.translation import gettext_lazy as _

ADMIN_USERNAME = os.getenv('DJANGO_SUPERUSER_USERNAME', default='admin')

GENDERS = (
    ('M', _('Male')),
    ('F', _('Female')),
)
