# Generated by Django 4.2.15 on 2024-09-02 11:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "languages",
            "0002_userlearninglanguage_user_usernativelanguage_user_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="userlearninglanguage",
            name="slug",
            field=models.SlugField(max_length=1024, unique=True, verbose_name="Slug"),
        ),
        migrations.AlterField(
            model_name="usernativelanguage",
            name="slug",
            field=models.SlugField(max_length=1024, unique=True, verbose_name="Slug"),
        ),
    ]
