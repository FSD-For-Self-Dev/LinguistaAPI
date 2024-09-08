# Generated by Django 4.2.15 on 2024-09-08 12:02

import apps.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_user_learning_languages_user_native_languages"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(
                max_length=32,
                validators=[
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Apostrophe, Space. Make sure name begin with a letter.",
                        regex="^(\\p{L}+)([\\p{L}'`’ ]*)$",
                    )
                ],
            ),
        ),
    ]
