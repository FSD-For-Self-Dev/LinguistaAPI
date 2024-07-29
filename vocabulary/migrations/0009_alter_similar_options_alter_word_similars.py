# Generated by Django 4.2.14 on 2024-07-29 09:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("vocabulary", "0008_alter_imageassociation_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="similar",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-from_word__created", "-created"),
                "verbose_name": "Похожее слово",
                "verbose_name_plural": "Похожие слова",
            },
        ),
        migrations.AlterField(
            model_name="word",
            name="similars",
            field=models.ManyToManyField(
                blank=True,
                help_text="Слова с похожим произношением или написанием",
                through="vocabulary.Similar",
                to="vocabulary.word",
                verbose_name="Похожие слова",
            ),
        ),
    ]
