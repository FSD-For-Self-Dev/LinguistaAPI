"""Utils to get something."""

import os
from typing import Any, Type

from django.db.models import Model
from django.core.exceptions import ObjectDoesNotExist

from dotenv import load_dotenv
from rest_framework.exceptions import NotFound

from apps.core.constants import ADMIN_USERNAME

load_dotenv()


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
            f'{obj_name} с id={pk} не найден.',
            code='object_not_exist',
        )


def get_admin_user(user_model: Model) -> Type[Model] | None:
    """Returns admin user or None if not found."""
    return user_model.objects.filter(username=ADMIN_USERNAME).first()


def get_yc_headers() -> dict[str, str]:
    """Returns headers for Yandex Translator API."""
    token = os.getenv('YC_YAM_TOKEN', default='')
    return {'Authorization': f'Bearer {token}'}
