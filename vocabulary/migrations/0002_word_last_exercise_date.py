# Generated by Django 4.2.10 on 2024-04-20 14:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vocabulary", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="word",
            name="last_exercise_date",
            field=models.DateTimeField(
                editable=False, null=True, verbose_name="Last exercise date"
            ),
        ),
    ]
