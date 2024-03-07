"""Утилиты приложения vocabulary."""

import re


def slugify_text(text):
    return re.sub("[-!?.,:'()]", '', text).replace(' ', '-').lower()


def slugify_text_author_fields(text, author, *args, **kwargs):
    """
    Генерация слага из уникального сочетания текстового поля и юзернейма автора.
    Убирает символы [-!?.,:'], приводит к нижнему регистру, заменяет пробелы на -,
    работает с любым алфавитным набором (не только с латиницей, в отличие от slugify).
    """
    return f'{slugify_text(text)}-{author.username}'


def slugify_text_word_fields(text, word, *args, **kwargs):
    """
    Генерация слага из уникального сочетания текстового поля и слага слова,
    к которому прекреплен объект.
    Убирает символы [-!?.,:'], приводит к нижнему регистру, заменяет пробелы на -,
    работает с любым алфавитным набором (не только с латиницей, в отличие от slugify).
    """
    return f'{slugify_text(text)}-{word.slug}'
