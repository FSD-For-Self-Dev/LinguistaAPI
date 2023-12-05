# Generated by Django 4.2.6 on 2023-11-19 17:42

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vocabulary', '0006_alter_usageexample_text_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usageexample',
            name='text',
            field=models.CharField(help_text='Пример использования слова или фразы', max_length=4096, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.MaxLengthValidator(512), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Пример использования'),
        ),
    ]
