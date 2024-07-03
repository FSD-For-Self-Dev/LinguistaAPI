"""Core abstract models."""

from collections import OrderedDict
from typing import Any

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from core.utils import slugify_text_fields


class GetObjectBySlugModelMixin:
    @classmethod
    def check_class_attrs(cls) -> None:
        assert hasattr(cls, 'slugify_func') and hasattr(cls, 'slugify_fields'), (
            'Set `slugify_func`, `slugify_fields` class attributes to use '
            'GetObjectBySlugModelMixin.'
        )

    @classmethod
    def get_slug_from_data(cls, *args, **kwargs) -> str:
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
    def get_object(cls, data: OrderedDict) -> Any:
        slug = cls.get_slug_from_data(**data)
        try:
            return cls.objects.get(slug=slug)
        except ObjectDoesNotExist:
            return None


class GetObjectModelMixin:
    get_object_by_fields = ('field',)

    @classmethod
    def check_class_attrs(cls) -> None:
        assert hasattr(
            cls, 'get_object_by_fields'
        ), 'Set `get_object_by_fields` class attributes to use GetObjectModelMixin.'

    @classmethod
    def get_object(cls, data: OrderedDict) -> Any:
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


def slug_filler(sender, instance, *args, **kwargs) -> None:
    """
    Fills slug field from slugify_fields
    (`slugify_func` and `slugify_fields` class attributes is needed).
    """
    slugify_data = [
        (
            instance.__getattribute__(field[0]).__getattribute__(field[1])
            if type(field) is tuple
            else instance.__getattribute__(field)
        )
        for field in sender.slugify_fields
    ]

    instance.slug = sender.slugify_func(*slugify_data, allow_unicode=True)
