# Generated by Django 4.2.10 on 2024-04-23 21:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vocabulary", "0002_word_last_exercise_date"),
    ]

    operations = [
        migrations.AlterField(
            model_name="collection",
            name="description",
            field=models.TextField(blank=True, max_length=128, verbose_name="Описание"),
        ),
    ]
