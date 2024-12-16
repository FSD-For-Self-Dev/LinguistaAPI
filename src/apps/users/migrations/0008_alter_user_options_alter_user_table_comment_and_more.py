# Generated by Django 4.2.15 on 2024-12-16 11:12

import apps.users.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("languages", "0009_alter_language_options_and_more"),
        ("users", "0007_alter_user_options_alter_user_table_comment_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={
                "get_latest_by": ("created", "date_joined"),
                "ordering": ("-date_joined",),
                "verbose_name": "Пользователь",
                "verbose_name_plural": "Пользователи",
            },
        ),
        migrations.AlterModelTableComment(
            name="user",
            table_comment="Пользователи",
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(max_length=254, verbose_name="Почта"),
        ),
        migrations.AlterField(
            model_name="user",
            name="gender",
            field=models.CharField(
                blank=True,
                choices=[("M", "Male"), ("F", "Female")],
                max_length=1,
                null=True,
                verbose_name="Пол",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=apps.users.models.user_profile_images_path,
                verbose_name="Картинка профиля",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="learning_languages",
            field=models.ManyToManyField(
                blank=True,
                related_name="learning_by",
                through="languages.UserLearningLanguage",
                to="languages.language",
                verbose_name="Изучаемые языки пользователей",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="native_languages",
            field=models.ManyToManyField(
                blank=True,
                related_name="native_for",
                through="languages.UserNativeLanguage",
                to="languages.language",
                verbose_name="Родные языки пользователей",
            ),
        ),
    ]
