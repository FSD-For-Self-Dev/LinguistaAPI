# Generated by Django 4.2.15 on 2024-12-16 11:12

import apps.languages.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("languages", "0008_alter_language_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="language",
            options={
                "get_latest_by": ("name",),
                "ordering": ("-sorting", "name", "isocode"),
                "verbose_name": "Язык",
                "verbose_name_plural": "Языки",
            },
        ),
        migrations.AlterModelOptions(
            name="languagecoverimage",
            options={
                "ordering": ("-created", "-modified"),
                "verbose_name": "Картинка языка",
                "verbose_name_plural": "Картинки языков",
            },
        ),
        migrations.AlterModelOptions(
            name="userlearninglanguage",
            options={
                "ordering": ("-created", "-modified"),
                "verbose_name": "Изучаемый язык пользователя",
                "verbose_name_plural": "Изучаемые языки пользователя",
            },
        ),
        migrations.AlterModelOptions(
            name="usernativelanguage",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Родной язык пользователя",
                "verbose_name_plural": "Родные языки пользователя",
            },
        ),
        migrations.AlterModelTableComment(
            name="language",
            table_comment="Языки",
        ),
        migrations.AlterModelTableComment(
            name="languagecoverimage",
            table_comment="Картинки доступные для обновления обложки изучаемого языка",
        ),
        migrations.AlterModelTableComment(
            name="userlearninglanguage",
            table_comment="Изучаемые языки пользователей",
        ),
        migrations.AlterModelTableComment(
            name="usernativelanguage",
            table_comment="Родные языки пользователей",
        ),
        migrations.AlterField(
            model_name="language",
            name="country",
            field=models.CharField(
                blank=True, max_length=256, verbose_name="Название страны"
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="country_en",
            field=models.CharField(
                blank=True, max_length=256, null=True, verbose_name="Название страны"
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="country_ru",
            field=models.CharField(
                blank=True, max_length=256, null=True, verbose_name="Название страны"
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="flag_icon",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="languages/flag_icons/",
                verbose_name="Иконка флага языка",
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="interface_available",
            field=models.BooleanField(
                default=False, verbose_name="Язык доступен для перевода интерфейса"
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="isocode",
            field=models.CharField(
                help_text="2 or 3 character language code with 2 character country code",
                max_length=8,
                unique=True,
                verbose_name="ISO 639-1 код языка",
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="learning_available",
            field=models.BooleanField(
                default=False, verbose_name="Язык доступен для добавления в изучаемые"
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="name",
            field=models.CharField(max_length=256, verbose_name="Название языка"),
        ),
        migrations.AlterField(
            model_name="language",
            name="name_en",
            field=models.CharField(
                max_length=256, null=True, verbose_name="Название языка"
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="name_local",
            field=models.CharField(
                blank=True,
                default="",
                max_length=256,
                verbose_name="Название языка (на этом языке)",
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="name_ru",
            field=models.CharField(
                max_length=256, null=True, verbose_name="Название языка"
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="sorting",
            field=models.PositiveIntegerField(
                default=0,
                help_text="Увеличьте, чтобы поднять в списке",
                verbose_name="Порядок сортировки",
            ),
        ),
        migrations.AlterField(
            model_name="languagecoverimage",
            name="image",
            field=models.ImageField(
                upload_to=apps.languages.models.language_images_path,
                verbose_name="Картинка языка",
            ),
        ),
        migrations.AlterField(
            model_name="languagecoverimage",
            name="language",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="images",
                to="languages.language",
                verbose_name="Язык",
            ),
        ),
        migrations.AlterField(
            model_name="userlearninglanguage",
            name="language",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="learning_by_detail",
                to="languages.language",
                verbose_name="Язык",
            ),
        ),
        migrations.AlterField(
            model_name="userlearninglanguage",
            name="level",
            field=models.CharField(
                blank=True,
                default="",
                max_length=256,
                null=True,
                verbose_name="Уровень владения",
            ),
        ),
        migrations.AlterField(
            model_name="userlearninglanguage",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="learning_languages_detail",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Пользователь",
            ),
        ),
        migrations.AlterField(
            model_name="usernativelanguage",
            name="language",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="native_for_detail",
                to="languages.language",
                verbose_name="Язык",
            ),
        ),
        migrations.AlterField(
            model_name="usernativelanguage",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="native_languages_detail",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Пользователь",
            ),
        ),
    ]
