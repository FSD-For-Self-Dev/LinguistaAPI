# Generated by Django 4.2.15 on 2024-09-04 14:57

import apps.core.models
import apps.core.validators
import django.core.validators
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("vocabulary", "0006_alter_collection_slug_alter_collection_title_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="WordType",
            fields=[
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="Date created"
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True, null=True, verbose_name="Date modified"
                    ),
                ),
                (
                    "slug",
                    models.SlugField(max_length=1024, unique=True, verbose_name="Slug"),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=64,
                        unique=True,
                        validators=[
                            django.core.validators.MinLengthValidator(1),
                            apps.core.validators.CustomRegexValidator(
                                message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure word begin with a letter.",
                                regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() ]*)$",
                            ),
                        ],
                        verbose_name="Word type name",
                    ),
                ),
                (
                    "name_ru",
                    models.CharField(
                        max_length=64,
                        null=True,
                        unique=True,
                        validators=[
                            django.core.validators.MinLengthValidator(1),
                            apps.core.validators.CustomRegexValidator(
                                message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure word begin with a letter.",
                                regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() ]*)$",
                            ),
                        ],
                        verbose_name="Word type name",
                    ),
                ),
                (
                    "name_en",
                    models.CharField(
                        max_length=64,
                        null=True,
                        unique=True,
                        validators=[
                            django.core.validators.MinLengthValidator(1),
                            apps.core.validators.CustomRegexValidator(
                                message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure word begin with a letter.",
                                regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() ]*)$",
                            ),
                        ],
                        verbose_name="Word type name",
                    ),
                ),
            ],
            options={
                "verbose_name": "Word type",
                "verbose_name_plural": "Word types",
                "db_table_comment": "Word or phrase types",
                "ordering": ("-created", "-modified", "-id"),
                "get_latest_by": ("created", "modified"),
            },
            bases=(
                apps.core.models.GetObjectBySlugModelMixin,
                apps.core.models.WordsCountMixin,
                models.Model,
            ),
        ),
        migrations.DeleteModel(
            name="Type",
        ),
        migrations.AlterField(
            model_name="word",
            name="types",
            field=models.ManyToManyField(
                blank=True,
                related_name="words",
                to="vocabulary.wordtype",
                verbose_name="WordType",
            ),
        ),
    ]
