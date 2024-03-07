# Generated by Django 4.2.8 on 2024-02-25 08:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("exercises", "0002_alter_exercise_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="exercise",
            options={
                "get_latest_by": ["created", "modified"],
                "ordering": ["-created"],
                "verbose_name": "Упражнение",
                "verbose_name_plural": "Упражнения",
            },
        ),
        migrations.AlterModelOptions(
            name="favoriteexercise",
            options={
                "get_latest_by": ["created"],
                "ordering": ["-created"],
                "verbose_name": "Избранное упражнение",
                "verbose_name_plural": "Избранные упражнения",
            },
        ),
        migrations.AlterField(
            model_name="exercise",
            name="description",
            field=models.CharField(max_length=4096, verbose_name="Описание"),
        ),
        migrations.AlterField(
            model_name="exercise",
            name="name",
            field=models.CharField(max_length=256, verbose_name="Название упражнения"),
        ),
        migrations.AlterField(
            model_name="favoriteexercise",
            name="exercise",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="favorite_for",
                to="exercises.exercise",
                verbose_name="Упражнение",
            ),
        ),
    ]
