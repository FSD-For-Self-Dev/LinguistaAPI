# Generated by Django 4.2.14 on 2024-08-01 08:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("vocabulary", "0009_alter_similar_options_alter_word_similars"),
        ("exercises", "0010_alter_exercisehistorydetails_task_translation_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="exercisehistorydetails",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Пошаговая история прохождения упражнения",
                "verbose_name_plural": "Пошаговая история прохождения упражнений",
            },
        ),
        migrations.AlterModelOptions(
            name="hint",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Подсказка",
                "verbose_name_plural": "Подсказки",
            },
        ),
        migrations.AlterModelOptions(
            name="translatoruserdefaultsettings",
            options={
                "verbose_name": "Настройки пользователя по умолчанию для упражнения Переводчик",
                "verbose_name_plural": "Настройки пользователей по умолчанию для упражнения Переводчик",
            },
        ),
        migrations.AlterModelOptions(
            name="usersexerciseshistory",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Прохождение упражнения пользователем",
                "verbose_name_plural": "Прохождения упражнений пользователем",
            },
        ),
        migrations.AlterModelOptions(
            name="wordset",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-last_exercise_date", "-created"),
                "verbose_name": "Набор слов",
                "verbose_name_plural": "Наборы слов",
            },
        ),
        migrations.AlterModelOptions(
            name="wordsupdatehistory",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "История изменения статуса активности слова",
                "verbose_name_plural": "История изменения статуса активности слов",
            },
        ),
        migrations.AlterModelTableComment(
            name="exercise",
            table_comment="Упражнение со словами",
        ),
        migrations.AlterModelTableComment(
            name="exercisehistorydetails",
            table_comment="Ответы пользователя в подходе",
        ),
        migrations.AlterModelTableComment(
            name="favoriteexercise",
            table_comment="Избранные упражнения",
        ),
        migrations.AlterModelTableComment(
            name="hint",
            table_comment="Подсказки досутпные для пользователей в упражнениях",
        ),
        migrations.AlterModelTableComment(
            name="translatoruserdefaultsettings",
            table_comment="Настройки для упражнения Переводчик применяемый по умолчанию для пользователя",
        ),
        migrations.AlterModelTableComment(
            name="usersexerciseshistory",
            table_comment="История прохождения упражнений пользователем",
        ),
        migrations.AlterModelTableComment(
            name="wordset",
            table_comment="Набор доступных для упражнения слов для быстрого старта",
        ),
        migrations.AlterModelTableComment(
            name="wordsupdatehistory",
            table_comment="История изменения статуса активности слов",
        ),
        migrations.AlterField(
            model_name="exercise",
            name="available",
            field=models.BooleanField(
                default=False,
                verbose_name="Упражнение доступно для прохождения пользователями",
            ),
        ),
        migrations.AlterField(
            model_name="exercise",
            name="constraint_description",
            field=models.CharField(
                blank=True, max_length=512, verbose_name="Описание ограничения"
            ),
        ),
        migrations.AlterField(
            model_name="exercise",
            name="hints_available",
            field=models.ManyToManyField(
                blank=True,
                related_name="exercises",
                to="exercises.hint",
                verbose_name="Подсказки доступные в упражнении",
            ),
        ),
        migrations.AlterField(
            model_name="exercise",
            name="icon",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="exercises/icons/",
                verbose_name="Иконка упражнения",
            ),
        ),
        migrations.AlterField(
            model_name="exercisehistorydetails",
            name="answer_time",
            field=models.TimeField(
                blank=True, null=True, verbose_name="Время ответа пользователя"
            ),
        ),
        migrations.AlterField(
            model_name="exercisehistorydetails",
            name="approach",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="details",
                to="exercises.usersexerciseshistory",
                verbose_name="Подход",
            ),
        ),
        migrations.AlterField(
            model_name="exercisehistorydetails",
            name="hints_used",
            field=models.ManyToManyField(
                blank=True,
                related_name="history",
                to="exercises.hint",
                verbose_name="Использованные подсказки",
            ),
        ),
        migrations.AlterField(
            model_name="exercisehistorydetails",
            name="task_translation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="exercises_history",
                to="vocabulary.wordtranslation",
                verbose_name="Перевод слова",
            ),
        ),
        migrations.AlterField(
            model_name="exercisehistorydetails",
            name="verdict",
            field=models.CharField(
                choices=[
                    ("C", "Правильно"),
                    ("I", "Неправильно"),
                    ("SC", "Почти правильно"),
                ],
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name="hint",
            name="code",
            field=models.CharField(
                max_length=32, unique=True, verbose_name="Короткий код подсказки"
            ),
        ),
        migrations.AlterField(
            model_name="hint",
            name="description",
            field=models.CharField(max_length=128, verbose_name="Описание подсказки"),
        ),
        migrations.AlterField(
            model_name="hint",
            name="name",
            field=models.CharField(
                max_length=32, unique=True, verbose_name="Название подсказки"
            ),
        ),
        migrations.AlterField(
            model_name="translatoruserdefaultsettings",
            name="from_language",
            field=models.CharField(
                choices=[
                    ("LTN", "С изучаемого языка"),
                    ("NTL", "С родного языка"),
                    ("LTL", "С изучаемого языка на изучаемый"),
                    ("A", "Попеременно"),
                ],
                default="LTN",
                max_length=32,
                verbose_name="Перевод с изучаемого или родного языка",
            ),
        ),
        migrations.AlterField(
            model_name="translatoruserdefaultsettings",
            name="mode",
            field=models.CharField(
                choices=[
                    ("FI", "Свободный ввод (одного перевода достаточно)"),
                    ("FIM", "Свободный ввод (максимальное кол-во переводов)"),
                    ("V", "Выбор из вариантов ответа"),
                ],
                default="FI",
                max_length=32,
                verbose_name="Выбранный режим прохождения упражнения",
            ),
        ),
        migrations.AlterField(
            model_name="translatoruserdefaultsettings",
            name="repetitions_amount",
            field=models.SmallIntegerField(
                default=1, verbose_name="Количество повторений каждого слова"
            ),
        ),
        migrations.AlterField(
            model_name="translatoruserdefaultsettings",
            name="answer_time_limit",
            field=models.TimeField(
                blank=True, null=True, verbose_name="Установленное ограничение времени"
            ),
        ),
        migrations.AlterField(
            model_name="usersexerciseshistory",
            name="complete_time",
            field=models.TimeField(
                blank=True, null=True, verbose_name="Время прохождения упражнения"
            ),
        ),
        migrations.AlterField(
            model_name="usersexerciseshistory",
            name="corrects_amount",
            field=models.IntegerField(verbose_name="Количество правильных ответов"),
        ),
        migrations.AlterField(
            model_name="usersexerciseshistory",
            name="hints_available",
            field=models.ManyToManyField(
                blank=True,
                related_name="approaches",
                to="exercises.hint",
                verbose_name="Подсказки доступные в этом подходе",
            ),
        ),
        migrations.AlterField(
            model_name="usersexerciseshistory",
            name="incorrects_amount",
            field=models.IntegerField(verbose_name="Количество неправильных ответов"),
        ),
        migrations.AlterField(
            model_name="usersexerciseshistory",
            name="mode",
            field=models.CharField(
                choices=[
                    ("FI", "Свободный ввод (одного перевода достаточно)"),
                    ("FIM", "Свободный ввод (максимальное кол-во переводов)"),
                    ("V", "Выбор из вариантов ответа"),
                ],
                default="FI",
                max_length=3,
                verbose_name="Выбранный режим прохождения упражнения",
            ),
        ),
        migrations.AlterField(
            model_name="usersexerciseshistory",
            name="answer_time_limit",
            field=models.TimeField(
                blank=True, null=True, verbose_name="Установленное ограничение времени"
            ),
        ),
        migrations.AlterField(
            model_name="usersexerciseshistory",
            name="words_amount",
            field=models.IntegerField(
                verbose_name="Количество слов пройденных в упражнении"
            ),
        ),
        migrations.AlterField(
            model_name="wordset",
            name="name",
            field=models.CharField(max_length=64, verbose_name="Название набора слов"),
        ),
        migrations.AlterField(
            model_name="wordset",
            name="words",
            field=models.ManyToManyField(
                related_name="sets", to="vocabulary.word", verbose_name="Слова набора"
            ),
        ),
        migrations.AlterField(
            model_name="wordsupdatehistory",
            name="approach",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="words_updates",
                to="exercises.usersexerciseshistory",
                verbose_name="Подход",
            ),
        ),
    ]
