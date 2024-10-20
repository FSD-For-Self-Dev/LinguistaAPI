# Generated by Django 4.2.15 on 2024-09-01 10:21

import apps.vocabulary.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vocabulary", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="imageassociation",
            name="image_url",
            field=models.CharField(
                blank=True, max_length=512, null=True, verbose_name="Image hotlink"
            ),
        ),
        migrations.AlterField(
            model_name="imageassociation",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=apps.vocabulary.models.image_associations_path,
                verbose_name="Картинка",
            ),
        ),
    ]
