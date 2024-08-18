"""Users models."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext as _
from django.db.models.signals import pre_save
from django.dispatch import receiver

from core.constants import GENDERS
from core.models import (
    CreatedModel,
    ModifiedModel,
    SlugModel,
    GetObjectBySlugModelMixin,
    slug_filler,
)
from languages.models import Language


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
        upload_to='users/profile-images/',
        blank=True,
        null=True,
    )
    native_languages = models.ManyToManyField(
        Language,
        through='UserNativeLanguage',
        related_name='native_for',
        verbose_name=_('Users native languages'),
        blank=True,
    )
    learning_languages = models.ManyToManyField(
        Language,
        through='UserLearningLanguage',
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


class UserDefaultWordsView(CreatedModel):
    """Default word cards view for the user."""

    STANDART = 'standart'
    SHORT = 'short'
    LONG = 'long'
    VIEW_OPTIONS = [
        (STANDART, _('Standart')),
        (SHORT, _('Short')),
        (LONG, _('Long')),
    ]

    user = models.ForeignKey(
        User,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='words_view_setting',
    )
    words_view = models.CharField(
        _('Word cards view'),
        max_length=8,
        choices=VIEW_OPTIONS,
        blank=False,
        default=STANDART,
    )

    class Meta:
        verbose_name = _('User default word cards view setting')
        verbose_name_plural = _('User default word cards view settings')
        db_table_comment = _('Default word cards view for the user')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [models.UniqueConstraint('user', name='unique_user_words_view')]

    def __str__(self) -> str:
        return f'Default words view for user {self.user} is {self.words_view}'


class UserLearningLanguage(
    GetObjectBySlugModelMixin,
    SlugModel,
    CreatedModel,
    ModifiedModel,
):
    """Users learning languages."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.CASCADE,
        related_name='learning_by_detail',
    )
    user = models.ForeignKey(
        User,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='learning_languages_detail',
    )
    level = models.CharField(
        _('Level of knowledge'),
        max_length=256,
        null=True,
        blank=True,
        default='',
    )
    cover = models.ImageField(
        _('Learning language cover image'),
        upload_to='users/languages/images/',
        blank=True,
        null=True,
    )

    slugify_fields = ('user', ('language', 'name'))

    class Meta:
        verbose_name = _('User learning language')
        verbose_name_plural = _('User learning languages')
        db_table_comment = _('Users learning languages')
        ordering = ('-created', '-modified')
        constraints = [
            models.UniqueConstraint(
                'language', 'user', name='unique_user_learning_language'
            )
        ]

    def __str__(self) -> str:
        return f'{self.user} studies {self.language}'


class UserNativeLanguage(SlugModel, CreatedModel):
    """Users native languages."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    language = models.ForeignKey(
        Language,
        verbose_name=_('Language'),
        on_delete=models.CASCADE,
        related_name='native_for_detail',
    )
    user = models.ForeignKey(
        User,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='native_languages_detail',
    )

    slugify_fields = ('user', ('language', 'name'))

    class Meta:
        verbose_name = _('User native language')
        verbose_name_plural = _('User native languages')
        db_table_comment = _('Users native languages')
        ordering = ('-created',)
        get_latest_by = ('created',)
        constraints = [
            models.UniqueConstraint(
                'language', 'user', name='unique_user_native_language'
            )
        ]

    def __str__(self) -> str:
        return f"{self.user}'s native language is {self.language}"


@receiver(pre_save, sender=UserLearningLanguage)
@receiver(pre_save, sender=UserNativeLanguage)
def fill_slug(sender, instance, *args, **kwargs) -> None:
    """Fill slug field before save instance."""
    return slug_filler(sender, instance, *args, **kwargs)
