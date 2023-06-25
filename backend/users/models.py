from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        unique=True
    )
    # image = models.ImageField(
    #     upload_to='users/images/',
    #     verbose_name='Фото',
    #     help_text='Загрузите картинку профиля',
    #     blank=True,
    #     null=True
    # )

    class Meta:
        ordering = ['-date_joined']
