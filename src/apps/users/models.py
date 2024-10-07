"""Users app models."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _

from apps.core.validators import CustomRegexValidator
from apps.core.models import (
    CreatedModel,
    ModifiedModel,
)
from utils.images import compress

from .constants import (
    GENDERS,
    REGEX_NAME_MASK,
    REGEX_NAME_MASK_DETAIL,
    UsersLengthLimits,
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
    first_name = models.CharField(
        max_length=UsersLengthLimits.FIRST_NAME_MAX_LENGTH,
        validators=(
            CustomRegexValidator(regex=REGEX_NAME_MASK, message=REGEX_NAME_MASK_DETAIL),
        ),
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

    def save(self, *args, **kwargs) -> None:
        """Compress profile image file before saving it."""
        if self.image:
            self.image = compress(self.image)
        return super().save(*args, **kwargs)

    def words_in_vocabulary(self) -> int:
        """Returns words in user's vocabulary amount."""
        return self.words.count()
