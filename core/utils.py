"""Core utils."""

from django.utils.text import slugify


def slugify_text_fields(*args, **kwargs):
    return '-'.join([slugify(text, allow_unicode=True) for text in args])
