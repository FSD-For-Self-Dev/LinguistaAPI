"""Utils to generate something."""

from django.utils.text import slugify


def slugify_text_fields(*args, **kwargs) -> str:
    """Generate slug from one and more fields."""
    return '-'.join([slugify(text, allow_unicode=True) for text in args])
