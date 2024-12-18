# Generated by Django 4.2.15 on 2024-09-01 09:26

import apps.core.models
import apps.languages.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Language",
            fields=[
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
                    models.CharField(max_length=256, verbose_name="Название языка"),
                ),
                (
                    "name_ru",
                    models.CharField(
                        max_length=256, null=True, verbose_name="Название языка"
                    ),
                ),
                (
                    "name_en",
                    models.CharField(
                        max_length=256, null=True, verbose_name="Название языка"
                    ),
                ),
                (
                    "name_local",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=256,
                        verbose_name="Название языка (на этом языке)",
                    ),
                ),
                (
                    "isocode",
                    models.CharField(
                        help_text="2 символьный код языка без страны",
                        max_length=8,
                        unique=True,
                        verbose_name="ISO 639-1 код языка",
                    ),
                ),
                (
                    "sorting",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Увеличьте, чтобы поднять в списке",
                        verbose_name="Порядок сортировки",
                    ),
                ),
                (
                    "learning_available",
                    models.BooleanField(
                        default=False,
                        verbose_name="Язык доступен для добавления в изучаемые",
                    ),
                ),
                (
                    "interface_available",
                    models.BooleanField(
                        default=False,
                        verbose_name="Язык доступен для перевода интерфейса",
                    ),
                ),
                (
                    "flag_icon",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="languages/flag_icons/",
                        verbose_name="Иконка флага языка",
                    ),
                ),
            ],
            options={
                "verbose_name": "Язык",
                "verbose_name_plural": "Языки",
                "db_table_comment": "Языки",
                "ordering": ("-sorting", "name", "isocode"),
            },
            bases=(apps.core.models.WordsCountMixin, models.Model),
        ),
        migrations.CreateModel(
            name="LanguageCoverImage",
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
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        upload_to=apps.languages.models.language_images_path,
                        verbose_name="Картинка языка",
                    ),
                ),
                (
                    "language",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="languages.language",
                        verbose_name="Язык",
                    ),
                ),
            ],
            options={
                "verbose_name": "Картинка языка",
                "verbose_name_plural": "Картинки языков",
                "db_table_comment": "Картинки доступные для обновления обложки изучаемого языка",
                "ordering": ("-created", "-modified"),
            },
        ),
        migrations.CreateModel(
            name="UserNativeLanguage",
            fields=[
                (
                    "created",
                    models.DateTimeField(
                        auto_now_add=True, db_index=True, verbose_name="Date created"
                    ),
                ),
                ("slug", models.SlugField(unique=True, verbose_name="Slug")),
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
                    "language",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="native_for_detail",
                        to="languages.language",
                        verbose_name="Язык",
                    ),
                ),
            ],
            options={
                "verbose_name": "Родной язык",
                "verbose_name_plural": "Родные языки",
                "db_table_comment": "Родные языки",
                "ordering": ("-created",),
                "get_latest_by": ("created",),
            },
        ),
        migrations.CreateModel(
            name="UserLearningLanguage",
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
                ("slug", models.SlugField(unique=True, verbose_name="Slug")),
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
                    "level",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=256,
                        null=True,
                        verbose_name="Уровень владения",
                    ),
                ),
                (
                    "cover",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="covers",
                        to="languages.languagecoverimage",
                        verbose_name="Обложка изучаемого языка",
                    ),
                ),
                (
                    "language",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="learning_by_detail",
                        to="languages.language",
                        verbose_name="Язык",
                    ),
                ),
            ],
            options={
                "verbose_name": "Изучаемый язык",
                "verbose_name_plural": "Изучаемые языки",
                "db_table_comment": "Изучаемые языки",
                "ordering": ("-created", "-modified"),
            },
            bases=(apps.core.models.GetObjectBySlugModelMixin, models.Model),
        ),
    ]
