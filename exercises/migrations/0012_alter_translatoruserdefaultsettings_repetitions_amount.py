# Generated by Django 4.2.10 on 2024-04-22 10:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("exercises", "0011_usersexerciseshistory_hints_available"),
    ]

    operations = [
        migrations.AlterField(
            model_name="translatoruserdefaultsettings",
            name="repetitions_amount",
            field=models.SmallIntegerField(
                default=1, verbose_name="Every word repetitions amount"
            ),
        ),
    ]
