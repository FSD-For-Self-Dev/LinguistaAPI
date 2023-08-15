"""Конфигурация приложения vocabulary."""

from django.apps import AppConfig


class VocabularyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vocabulary'
    verbose_name = 'Словарь'
