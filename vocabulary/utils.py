"""Утилиты приложения vocabulary."""

from django.template.defaultfilters import slugify

def slugify_text_author_fields(self):
    """Генерация слагов для слов."""
    slugified_text = slugify(self.text)
    return f'{slugified_text}-{self.author.id}'

def slugify_title_author_fields(self):
    """Генерация слагов для коллекций."""
    slugified_title = slugify(self.title)
    return f'{slugified_title}-{self.author.id}'
