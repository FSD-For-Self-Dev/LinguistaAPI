# Generated by Django 4.2.15 on 2024-09-01 09:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "languages",
            "0002_userlearninglanguage_user_usernativelanguage_user_and_more",
        ),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="learning_languages",
            field=models.ManyToManyField(
                blank=True,
                related_name="learning_by",
                through="languages.UserLearningLanguage",
                to="languages.language",
                verbose_name="Изучаемые языки",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="native_languages",
            field=models.ManyToManyField(
                blank=True,
                related_name="native_for",
                through="languages.UserNativeLanguage",
                to="languages.language",
                verbose_name="Родные языки",
            ),
        ),
    ]
