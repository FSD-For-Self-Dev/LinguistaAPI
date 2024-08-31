"""Core abstract models, model mixins."""

from collections import OrderedDict
from typing import Type

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from utils.generators import slugify_text_fields
from config.settings import AUTH_USER_MODEL


class GetObjectBySlugModelMixin:
    """
    Custom mixin to use in Model.
    Adds `get_object` method to get object from its slug.
    Use within custom AlreadyExistSerializerHandler serializer mixin
    to avoid IntegrityError during create, update.
    `slugify_func`, `slugify_fields` class attributes must be set.
    `slugify_func` - slug generator function.
    `slugify_fields` - fields to generate slug from,
    must be an iterable with fields names (str or tuple[str, str] when second element
    is attribute for first), example: slugify_fields = ('title', ('author', 'name')).
    """

    @classmethod
    def check_class_attrs(cls) -> None:
        """Check if required class attributes are passed."""
        assert hasattr(cls, 'slugify_func') and hasattr(cls, 'slugify_fields'), (
            'Set `slugify_func`, `slugify_fields` class attributes to use '
            'GetObjectBySlugModelMixin.'
        )

    @classmethod
    def get_slug_from_data(cls, *args, **kwargs) -> str:
        """
        Collect slug fields from passed data, return slug generated in `slugify_func`.
        """
        cls.check_class_attrs()
        _slugify_data = []
        for field in cls.slugify_fields:
            try:
                value = (
                    kwargs.get(field[0]).__getattribute__(field[1])
                    if type(field) is tuple
                    else kwargs.get(field)
                )
                _slugify_data.append(value)
            except KeyError:
                raise AssertionError(
                    f'Can not get slug from data. Make sure {field} are passed in '
                    'data.'
                )
        return cls.slugify_func(*_slugify_data)

    @classmethod
    def get_object(cls, data: OrderedDict) -> Type[models.Model] | None:
        """Returns object gotten by slug or None if ObjectDoesNotExist is raised."""
        slug = cls.get_slug_from_data(**data)
        try:
            return cls.objects.get(slug=slug)
        except ObjectDoesNotExist:
            return None


class GetObjectModelMixin:
    """
    Custom mixin to use in Model.
    Adds `get_object` method to get object from specified fields.
    Use within custom AlreadyExistSerializerHandler serializer mixin
    to avoid IntegrityError during create, update.
    `get_object_by_fields` class attribute must be set.
    `get_object_by_fields` - fields to get object by, must be an iterable
    with fields names (str), example: get_object_by_fields = ('field1', 'field2').
    """

    @classmethod
    def check_class_attrs(cls) -> None:
        """Check if required class attributes are passed."""
        assert hasattr(
            cls, 'get_object_by_fields'
        ), 'Set `get_object_by_fields` class attributes to use GetObjectModelMixin.'

    @classmethod
    def get_object(cls, data: OrderedDict) -> Type[models.Model] | None:
        """
        Collect required fields from passed data, return object gotten by this fields
        or None if ObjectDoesNotExist is raised.
        """
        cls.check_class_attrs()
        get_by_fields = {}
        for field in cls.get_object_by_fields:
            assert (
                field in data
            ), f'Can not get object from data. Make sure {field} are passed in data.'
            get_by_fields[field] = data[field]
        try:
            return cls.objects.get(**get_by_fields)
        except ObjectDoesNotExist:
            return None


class WordsCountMixin:
    """Custom model mixin to add `words_count` method"""

    def words_count(self) -> int:
        """
        Returns object related words amount.
        Related name of word objects must be `words`.
        """
        return self.words.count()


class CreatedModel(models.Model):
    """Abstract base class to add date created field."""

    created = models.DateTimeField(
        _('Date created'),
        editable=False,
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        abstract = True


class ModifiedModel(models.Model):
    """Abstract base class to add date modified field."""

    modified = models.DateTimeField(
        _('Date modified'),
        blank=True,
        null=True,
        auto_now=True,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs) -> None:
        """On save, update timestamps."""
        self.modified = timezone.now()
        return super().save(*args, **kwargs)


class SlugModel(models.Model):
    """Abstract base class to add unique not null slug field."""

    slugify_func = slugify_text_fields

    slug = models.SlugField(
        _('Slug'),
        unique=True,
        blank=False,
        null=False,
    )

    class Meta:
        abstract = True


class UserRelatedModel(CreatedModel):
    """Abstract model to add `user` field for related user."""

    user = models.ForeignKey(
        AUTH_USER_MODEL,
        verbose_name=_('User'),
        on_delete=models.CASCADE,
        related_name='%(class)s',
    )

    class Meta:
        abstract = True


class AuthorModel(models.Model):
    """Abstract model to add `author` field for related user."""

    author = models.ForeignKey(
        AUTH_USER_MODEL,
        verbose_name=_('Author'),
        on_delete=models.CASCADE,
        related_name='%(class)ss',
    )

    class Meta:
        abstract = True
