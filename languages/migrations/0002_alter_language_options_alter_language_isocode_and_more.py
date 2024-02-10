# Generated by Django 4.2.8 on 2023-12-15 18:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('languages', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='language',
            options={'ordering': ('-sorting', 'name', 'isocode'), 'verbose_name': 'Language', 'verbose_name_plural': 'Languages'},
        ),
        migrations.AlterField(
            model_name='language',
            name='isocode',
            field=models.CharField(help_text='2 character language code without country', max_length=2, unique=True, verbose_name='ISO 639-1 Language code'),
        ),
        migrations.AlterField(
            model_name='language',
            name='name',
            field=models.CharField(max_length=256, verbose_name='Language name'),
        ),
        migrations.AlterField(
            model_name='language',
            name='name_local',
            field=models.CharField(blank=True, default='', max_length=256, verbose_name='Language name (in that language)'),
        ),
        migrations.AlterField(
            model_name='language',
            name='sorting',
            field=models.PositiveIntegerField(default=0, help_text='increase to show at top of the list', verbose_name='Sorting order'),
        ),
        migrations.AlterField(
            model_name='userlanguage',
            name='language',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='speakers', to='languages.language', verbose_name='Language'),
        ),
    ]
