''' Users models '''

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _

from core.constants import GENDERS


class User(AbstractUser):
    last_name = None

    email = models.EmailField(
        _('Email'),
        unique=True,
        blank=True
    )
    slug = models.SlugField(
        _('Slug'),
        max_length=255
    )
    gender = models.CharField(
        _('Gender'),
        max_length=1,
        choices=GENDERS,
        null=True,
        blank=True
    )
    image = models.ImageField(
        _('Profile image'),
        upload_to='users/profile-images/',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-date_joined']
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def words_in_vocabulary(self) -> int:
        return self.vocabulary.count()
