# Generated by Django 4.2.8 on 2024-02-25 08:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("languages", "0002_alter_language_options_alter_language_isocode_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="language",
            options={
                "ordering": ("-sorting", "name", "isocode"),
                "verbose_name": "Язык",
                "verbose_name_plural": "Языки",
            },
        ),
        migrations.AlterField(
            model_name="language",
            name="isocode",
            field=models.CharField(
                help_text="2 символьный код языка без страны",
                max_length=2,
                unique=True,
                verbose_name="ISO 639-1 код языка",
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="name",
            field=models.CharField(max_length=256, verbose_name="Название"),
        ),
        migrations.AlterField(
            model_name="language",
            name="name_local",
            field=models.CharField(
                blank=True,
                default="",
                max_length=256,
                verbose_name="Название (на этом языке)",
            ),
        ),
        migrations.AlterField(
            model_name="language",
            name="sorting",
            field=models.PositiveIntegerField(
                default=0,
                help_text="увеличьте, чтобы поднять в списке",
                verbose_name="Порядок сортировки",
            ),
        ),
        migrations.AlterField(
            model_name="userlanguage",
            name="language",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="speakers",
                to="languages.language",
                verbose_name="Язык",
            ),
        ),
    ]
