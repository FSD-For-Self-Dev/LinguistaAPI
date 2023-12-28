"""Утилиты приложения vocabulary."""

import re


def slugify_text_author_fields(text, author_id):
    """
    Генерация слага из уникального текстового поля и айди автора.
    Убирает символы [-!?.,:'], приводит к нижнему регистру, заменяет пробелы на -,
    работает с любым алфавитным набором (не только с латиницей, в отличие от slugify).
    """
    slugified_text = re.sub("[-!?.,:'()]", '', text).replace(' ', '-').lower()
    return f'{slugified_text}-{author_id}'
