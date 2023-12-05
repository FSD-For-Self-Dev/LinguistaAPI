# Generated by Django 4.2.6 on 2023-11-19 19:48

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vocabulary', '0009_alter_collection_title_alter_definition_text_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='words',
            field=models.ManyToManyField(blank=True, related_name='collections', through='vocabulary.WordsInCollections', to='vocabulary.word', verbose_name='Word in collection'),
        ),
        migrations.AlterField(
            model_name='type',
            name='name',
            field=models.CharField(max_length=64, unique=True, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Имя типа'),
        ),
        migrations.AlterField(
            model_name='type',
            name='name_en',
            field=models.CharField(max_length=64, null=True, unique=True, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Имя типа'),
        ),
        migrations.AlterField(
            model_name='type',
            name='name_ru',
            field=models.CharField(max_length=64, null=True, unique=True, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Имя типа'),
        ),
    ]
