# Generated by Django 4.2.6 on 2023-11-19 17:39

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vocabulary', '0004_remove_usageexample_unique_word_usage_example_in_user_voc_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='definition',
            name='unique_definition_in_user_voc',
        ),
        migrations.RemoveConstraint(
            model_name='usageexample',
            name='unique_word_usage_example_in_user_voc',
        ),
        migrations.AlterField(
            model_name='collection',
            name='title',
            field=models.CharField(max_length=256, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.MaxLengthValidator(32), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Название коллекции'),
        ),
        migrations.AlterField(
            model_name='definition',
            name='text',
            field=models.CharField(help_text='Определение слова или фразы', max_length=4096, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.MaxLengthValidator(1024), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Определение'),
        ),
        migrations.AlterField(
            model_name='definition',
            name='translation',
            field=models.CharField(blank=True, max_length=4096, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.MaxLengthValidator(1024), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Перевод определения'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=64, unique=True, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.MaxLengthValidator(32), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Имя тега'),
        ),
        migrations.AlterField(
            model_name='type',
            name='name',
            field=models.CharField(max_length=64, unique=True, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.MaxLengthValidator(64), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Имя типа'),
        ),
        migrations.AlterField(
            model_name='type',
            name='name_en',
            field=models.CharField(max_length=64, null=True, unique=True, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.MaxLengthValidator(64), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Имя типа'),
        ),
        migrations.AlterField(
            model_name='type',
            name='name_ru',
            field=models.CharField(max_length=64, null=True, unique=True, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.MaxLengthValidator(64), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Имя типа'),
        ),
        migrations.AlterField(
            model_name='word',
            name='text',
            field=models.CharField(max_length=4096, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.MaxLengthValidator(512), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Слово или фраза'),
        ),
        migrations.AlterField(
            model_name='wordtranslation',
            name='text',
            field=models.CharField(help_text='Перевод слова или фразы на другой язык', max_length=4096, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.MaxLengthValidator(512), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-я]+)([A-Za-zА-Яа-я-!?.,:' ]*)$")], verbose_name='Перевод'),
        ),
        migrations.AddConstraint(
            model_name='definition',
            constraint=models.UniqueConstraint(fields=('text', 'author'), name='unique_definition_in_user_voc'),
        ),
        migrations.AddConstraint(
            model_name='usageexample',
            constraint=models.UniqueConstraint(fields=('text', 'author'), name='unique_word_usage_example_in_user_voc'),
        ),
    ]
