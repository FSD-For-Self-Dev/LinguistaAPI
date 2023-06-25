from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Word(models.Model):
    """Слово"""


class Collection(models.Model):
    """Коллекция"""


class Exercise(models.Model):
    """Упражнение"""
