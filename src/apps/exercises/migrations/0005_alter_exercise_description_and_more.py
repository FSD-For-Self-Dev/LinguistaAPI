# Generated by Django 4.2.15 on 2024-12-16 09:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("vocabulary", "0019_alter_antonym_options_alter_collection_options_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("exercises", "0004_alter_exercise_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="exercise",
            name="description",
            field=models.CharField(max_length=4096, verbose_name="Description"),
        ),
        migrations.AlterField(
            model_name="exercisehistorydetails",
            name="task_word",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="exercises_history",
                to="vocabulary.word",
                verbose_name="Word",
            ),
        ),
        migrations.AlterField(
            model_name="favoriteexercise",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="favorite_exercises",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
        migrations.AlterField(
            model_name="translatoruserdefaultsettings",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="translator_settings",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
        migrations.AlterField(
            model_name="usersexerciseshistory",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="exercises_history",
                to=settings.AUTH_USER_MODEL,
                verbose_name="User",
            ),
        ),
        migrations.AlterField(
            model_name="wordset",
            name="last_exercise_date",
            field=models.DateTimeField(
                editable=False, null=True, verbose_name="Last exercise date"
            ),
        ),
        migrations.AlterField(
            model_name="wordsupdatehistory",
            name="activity_status",
            field=models.CharField(
                choices=[("I", "Inactive"), ("A", "Active"), ("M", "Mastered")],
                default="I",
                max_length=8,
                verbose_name="Activity status",
            ),
        ),
        migrations.AlterField(
            model_name="wordsupdatehistory",
            name="word",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="update_history",
                to="vocabulary.word",
                verbose_name="Word",
            ),
        ),
    ]
