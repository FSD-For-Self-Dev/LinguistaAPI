"""Модели приложения users."""

from django.contrib.auth.models import AbstractUser
from django.db import models

from core.constants import GENDERS


class User(AbstractUser):
    """Кастомная модель пользователя."""

    # исключаем из таблицы стобец "last_name"
    last_name = None

    email = models.EmailField(
        'Электронная почта',
        unique=True,
        help_text='Пользовательский email',
    )
    slug = models.SlugField(
        'Слаг',
        max_length=255,
        help_text='Слаг',
    )
    gender = models.CharField(
        'Пол',
        max_length=10,
        choices=GENDERS,
        null=True,
        help_text='Пол',
    )

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
