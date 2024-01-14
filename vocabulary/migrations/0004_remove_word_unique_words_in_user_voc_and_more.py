# Generated by Django 4.2.8 on 2023-12-27 14:57

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vocabulary', '0003_remove_collection_unique_user_collection_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='word',
            name='unique_words_in_user_voc',
        ),
        migrations.AlterField(
            model_name='collection',
            name='title',
            field=models.CharField(max_length=32, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='Collection title'),
        ),
        migrations.AlterField(
            model_name='definition',
            name='text',
            field=models.CharField(help_text='A definition of a word or phrase', max_length=1024, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='Definition'),
        ),
        migrations.AlterField(
            model_name='definition',
            name='translation',
            field=models.CharField(blank=True, max_length=1024, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='A translation of the definition'),
        ),
        migrations.AlterField(
            model_name='formsgroup',
            name='name',
            field=models.CharField(max_length=64, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='Group name'),
        ),
        migrations.AlterField(
            model_name='imageassociation',
            name='name',
            field=models.CharField(blank=True, max_length=64, validators=[django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='Image name'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(max_length=32, unique=True, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='Tag name'),
        ),
        migrations.AlterField(
            model_name='type',
            name='name',
            field=models.CharField(max_length=64, unique=True, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='Type name'),
        ),
        migrations.AlterField(
            model_name='type',
            name='name_en',
            field=models.CharField(max_length=64, null=True, unique=True, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='Type name'),
        ),
        migrations.AlterField(
            model_name='type',
            name='name_ru',
            field=models.CharField(max_length=64, null=True, unique=True, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='Type name'),
        ),
        migrations.AlterField(
            model_name='usageexample',
            name='text',
            field=models.CharField(help_text='An usage example of a word or phrase', max_length=1024, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='Usage example'),
        ),
        migrations.AlterField(
            model_name='usageexample',
            name='translation',
            field=models.CharField(blank=True, max_length=1024, validators=[django.core.validators.MinLengthValidator(2), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='A translation of the example'),
        ),
        migrations.AlterField(
            model_name='word',
            name='text',
            field=models.CharField(max_length=512, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='Word or phrase'),
        ),
        migrations.AlterField(
            model_name='wordtranslation',
            name='text',
            field=models.CharField(help_text='A translation of a word or phrase', max_length=512, validators=[django.core.validators.MinLengthValidator(1), django.core.validators.RegexValidator(message='Acceptable characters: Latin letters (A-Z, a-z), Cyrillic letters (А-Я, а-я), Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe. Make sure word begin with a letter.', regex="^([A-Za-zА-Яа-яёЁ]+)([A-Za-zА-Яа-я-!?.,:'ёЁ ]*)$")], verbose_name='Translation'),
        ),
        migrations.AddConstraint(
            model_name='word',
            constraint=models.UniqueConstraint(models.F('text'), models.F('author'), name='unique_words_in_user_voc'),
        ),
    ]
