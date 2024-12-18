# Generated by Django 4.2.15 on 2024-10-24 10:10

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("languages", "0003_alter_userlearninglanguage_slug_and_more"),
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
    ]
