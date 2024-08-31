"""Users app models."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _

from apps.core.constants import GENDERS
from apps.core.models import (
    CreatedModel,
    ModifiedModel,
)


def user_profile_images_path(user, filename) -> str:
    return f'users/profile-images/{user.username}/{filename}'


class User(AbstractUser, CreatedModel, ModifiedModel):
    """User custom model."""

    last_name = None

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    email = models.EmailField(
        _('Email'),
        blank=False,
    )
    gender = models.CharField(
        _('Gender'),
        max_length=1,
        choices=GENDERS,
        null=True,
        blank=True,
    )
    image = models.ImageField(
        _('Profile image'),
        upload_to=user_profile_images_path,
        blank=True,
        null=True,
    )
    native_languages = models.ManyToManyField(
        'languages.Language',
        through='languages.UserNativeLanguage',
        related_name='native_for',
        verbose_name=_('Users native languages'),
        blank=True,
    )
    learning_languages = models.ManyToManyField(
        'languages.Language',
        through='languages.UserLearningLanguage',
        related_name='learning_by',
        verbose_name=_('Users learning languages'),
        blank=True,
    )

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table_comment = _('Users')
        ordering = ('-date_joined',)
        get_latest_by = ('created', 'date_joined')

    def __str__(self) -> str:
        return self.username

    def words_in_vocabulary(self) -> int:
        """Returns words in user's vocabulary amount."""
        return self.words.count()
