# Generated by Django 4.2.15 on 2024-12-17 08:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vocabulary", "0020_alter_antonym_options_alter_collection_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="imageassociation",
            name="image_url",
            field=models.CharField(
                blank=True, max_length=512, null=True, verbose_name="Ссылка на картинку"
            ),
        ),
    ]
