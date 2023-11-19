"""Утилиты приложения vocabulary."""

def slugify_text_author_fields(self, text_field):
    """Генерация слагов для слов и коллекций."""
    slugified_text = text_field.replace(' ', '-')
    return f'{slugified_text}-{self.author.id}'
