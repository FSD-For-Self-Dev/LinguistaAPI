"""Утилиты приложения vocabulary."""

def slugify_text_author_fields(self):
    """Генерация слагов для слов."""
    without_spaces = self.text.replace(' ', '-')
    return f'{without_spaces}-{self.author.id}'
