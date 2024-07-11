"""Core utils."""

from typing import Any, Type

from django.db.models import Model
from django.utils.text import slugify
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.exceptions import NotFound

from .constants import ADMIN_USERNAME


def slugify_text_fields(*args, **kwargs) -> str:
    """Generate slug from one and more fields."""
    return '-'.join([slugify(text, allow_unicode=True) for text in args])


def get_object_by_pk(
    model: Model, pk: int, other_args: dict[str, Any] = {}
) -> Type[Model]:
    """
    Returns object gotten by passed id or NotFound raise.
    """
    try:
        obj = model.objects.get(pk=pk, **other_args)
        return obj
    except ObjectDoesNotExist:
        obj_name = model._meta.verbose_name
        raise NotFound(
            detail=f'{obj_name} с id={pk} не найден.',
            code=f'{model}_object_not_exist',
        )


def get_admin_user(user_model: Model) -> Type[Model] | None:
    """Returns admin user or None if not found."""
    return user_model.objects.filter(username=ADMIN_USERNAME).first()
