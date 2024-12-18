# Generated by Django 4.2.15 on 2024-12-16 11:12

import apps.core.validators
import apps.vocabulary.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("languages", "0009_alter_language_options_and_more"),
        ("vocabulary", "0019_alter_antonym_options_alter_collection_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="antonym",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-from_word__created", "-created"),
                "verbose_name": "Антоним",
                "verbose_name_plural": "Антонимы",
            },
        ),
        migrations.AlterModelOptions(
            name="collection",
            options={
                "get_latest_by": ("created", "modified"),
                "ordering": ("-created", "-modified", "-id"),
                "verbose_name": "Коллекция",
                "verbose_name_plural": "Коллекции",
            },
        ),
        migrations.AlterModelOptions(
            name="defaultwordcards",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Настройка вида карточек слов пользователя по умолчанию",
                "verbose_name_plural": "Настройки вида карточек слов пользователя по умолчанию",
            },
        ),
        migrations.AlterModelOptions(
            name="definition",
            options={
                "get_latest_by": ("created", "modified"),
                "ordering": ("-created", "-modified", "-id"),
                "verbose_name": "Определение",
                "verbose_name_plural": "Определения",
            },
        ),
        migrations.AlterModelOptions(
            name="favoritecollection",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Избранная коллекция",
                "verbose_name_plural": "Избранные коллекции",
            },
        ),
        migrations.AlterModelOptions(
            name="favoriteword",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Избранное слова",
                "verbose_name_plural": "Избранные слова",
            },
        ),
        migrations.AlterModelOptions(
            name="form",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-from_word__created", "-created"),
                "verbose_name": "Форма",
                "verbose_name_plural": "Формы",
            },
        ),
        migrations.AlterModelOptions(
            name="formgroup",
            options={
                "get_latest_by": ("created", "modified"),
                "ordering": ("-created", "-modified", "name"),
                "verbose_name": "Группа форм",
                "verbose_name_plural": "Группы форм",
            },
        ),
        migrations.AlterModelOptions(
            name="imageassociation",
            options={
                "get_latest_by": ("created", "modified"),
                "ordering": ("-created", "-modified"),
                "verbose_name": "Картинка-ассоциация",
                "verbose_name_plural": "Картинки-ассоциации",
            },
        ),
        migrations.AlterModelOptions(
            name="quoteassociation",
            options={
                "get_latest_by": ("created", "modified"),
                "ordering": ("-created", "-modified"),
                "verbose_name": "Цитата-ассоциация",
                "verbose_name_plural": "Цитаты-ассоциации",
            },
        ),
        migrations.AlterModelOptions(
            name="similar",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-from_word__created", "-created"),
                "verbose_name": "Похожее слово",
                "verbose_name_plural": "Похожие слова",
            },
        ),
        migrations.AlterModelOptions(
            name="synonym",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-from_word__created", "-created"),
                "verbose_name": "Синонимы",
                "verbose_name_plural": "Синонимы",
            },
        ),
        migrations.AlterModelOptions(
            name="usageexample",
            options={
                "get_latest_by": ("created", "modified"),
                "ordering": ("-created", "-modified"),
                "verbose_name": "Пример использования",
                "verbose_name_plural": "Примеры использования",
            },
        ),
        migrations.AlterModelOptions(
            name="word",
            options={
                "get_latest_by": ("created", "modified"),
                "ordering": ("-created", "-modified", "-id"),
                "verbose_name": "Слово или фраза",
                "verbose_name_plural": "Слова и фразы",
            },
        ),
        migrations.AlterModelOptions(
            name="worddefinitions",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Определение слова (промежуточная модель)",
                "verbose_name_plural": "Определения слов (промежуточная модель)",
            },
        ),
        migrations.AlterModelOptions(
            name="wordimageassociations",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Картинка-ассоциация слова (промежуточная модель)",
                "verbose_name_plural": "Картинки-ассоциации слов (промежуточная модель)",
            },
        ),
        migrations.AlterModelOptions(
            name="wordquoteassociations",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Цитата-ассоциация слова (промежуточная модель)",
                "verbose_name_plural": "Цитаты-ассоциации слов (промежуточная модель)",
            },
        ),
        migrations.AlterModelOptions(
            name="wordsformgroups",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Группа форм слова (промежуточная модель)",
                "verbose_name_plural": "Группы форм слов (промежуточная модель)",
            },
        ),
        migrations.AlterModelOptions(
            name="wordsincollections",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Слово, добавленное в коллекцию (промежуточная модель)",
                "verbose_name_plural": "Слова, добавленные в коллекции (промежуточная модель)",
            },
        ),
        migrations.AlterModelOptions(
            name="wordtag",
            options={
                "get_latest_by": ("created", "modified"),
                "ordering": ("-created", "-modified"),
                "verbose_name": "Теги слова",
                "verbose_name_plural": "Теги слова",
            },
        ),
        migrations.AlterModelOptions(
            name="wordtranslation",
            options={
                "get_latest_by": ("created", "modified"),
                "ordering": ("-created", "-modified"),
                "verbose_name": "Перевод",
                "verbose_name_plural": "Переводы",
            },
        ),
        migrations.AlterModelOptions(
            name="wordtranslations",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Перевод слова (промежуточная модель)",
                "verbose_name_plural": "Переводы слов (промежуточная модель)",
            },
        ),
        migrations.AlterModelOptions(
            name="wordtype",
            options={
                "get_latest_by": ("created", "modified"),
                "ordering": ("-created", "-modified", "-id"),
                "verbose_name": "Тип слова",
                "verbose_name_plural": "Типы слов",
            },
        ),
        migrations.AlterModelOptions(
            name="wordusageexamples",
            options={
                "get_latest_by": ("created",),
                "ordering": ("-created",),
                "verbose_name": "Пример использования слова (промежуточная модель)",
                "verbose_name_plural": "Примеры использования слов (промежуточная модель)",
            },
        ),
        migrations.AlterModelTableComment(
            name="antonym",
            table_comment="Слова-антонимы",
        ),
        migrations.AlterModelTableComment(
            name="collection",
            table_comment="Коллекции слов и фраз",
        ),
        migrations.AlterModelTableComment(
            name="defaultwordcards",
            table_comment="Вид карточек слов пользователя по умолчанию",
        ),
        migrations.AlterModelTableComment(
            name="definition",
            table_comment="Определения слов и фраз",
        ),
        migrations.AlterModelTableComment(
            name="favoritecollection",
            table_comment="Избранные коллекции",
        ),
        migrations.AlterModelTableComment(
            name="favoriteword",
            table_comment="Избранные слова",
        ),
        migrations.AlterModelTableComment(
            name="form",
            table_comment="Слова-формы",
        ),
        migrations.AlterModelTableComment(
            name="formgroup",
            table_comment="Группы форм существующие в языке",
        ),
        migrations.AlterModelTableComment(
            name="imageassociation",
            table_comment="Картинки-ассоциации слов и фраз",
        ),
        migrations.AlterModelTableComment(
            name="quoteassociation",
            table_comment="Цитаты-ассоциации слов и фраз",
        ),
        migrations.AlterModelTableComment(
            name="similar",
            table_comment="Похожие слова",
        ),
        migrations.AlterModelTableComment(
            name="synonym",
            table_comment="Слова-синонимы",
        ),
        migrations.AlterModelTableComment(
            name="usageexample",
            table_comment="Примеры использования слов и фраз",
        ),
        migrations.AlterModelTableComment(
            name="word",
            table_comment="Добавленные пользователями слова и фразы",
        ),
        migrations.AlterModelTableComment(
            name="worddefinitions",
            table_comment="Промежуточная модель для определений и слов",
        ),
        migrations.AlterModelTableComment(
            name="wordimageassociations",
            table_comment="Промежуточная модель для картинок-ассоциаций и слов",
        ),
        migrations.AlterModelTableComment(
            name="wordquoteassociations",
            table_comment="Промежуточная модель для цитат-ассоциаций и слов",
        ),
        migrations.AlterModelTableComment(
            name="wordsformgroups",
            table_comment="Промежуточная модель для слов и групп форм",
        ),
        migrations.AlterModelTableComment(
            name="wordsincollections",
            table_comment="Промежуточная модель для слов и коллекций",
        ),
        migrations.AlterModelTableComment(
            name="wordtag",
            table_comment="Теги слов или фраз",
        ),
        migrations.AlterModelTableComment(
            name="wordtranslation",
            table_comment="Переводы слов и фраз",
        ),
        migrations.AlterModelTableComment(
            name="wordtranslations",
            table_comment="Промежуточная модель для переводов и слов",
        ),
        migrations.AlterModelTableComment(
            name="wordtype",
            table_comment="Типы слов или фраз",
        ),
        migrations.AlterModelTableComment(
            name="wordusageexamples",
            table_comment="Промежуточная модель для примеров использования и слов",
        ),
        migrations.RemoveConstraint(
            model_name="word",
            name="unique_words_in_user_voc",
        ),
        migrations.AlterField(
            model_name="antonym",
            name="note",
            field=models.CharField(
                blank=True,
                help_text="Заметка для %(class)ss",
                max_length=256,
                verbose_name="Заметка",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="description",
            field=models.CharField(blank=True, max_length=128, verbose_name="Описание"),
        ),
        migrations.AlterField(
            model_name="collection",
            name="title",
            field=models.CharField(
                max_length=32,
                validators=[
                    django.core.validators.MinLengthValidator(1),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Digits Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. ",
                        regex="^([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Название коллекции",
            ),
        ),
        migrations.AlterField(
            model_name="collection",
            name="words",
            field=models.ManyToManyField(
                blank=True,
                related_name="collections",
                through="vocabulary.WordsInCollections",
                to="vocabulary.word",
                verbose_name="Слово, добавленное в коллекцию",
            ),
        ),
        migrations.AlterField(
            model_name="defaultwordcards",
            name="cards_type",
            field=models.CharField(
                choices=[
                    ("standart", "Стандартный"),
                    ("short", "Сокращенный"),
                    ("long", "Пролонгированный"),
                ],
                default="standart",
                max_length=8,
                verbose_name="Word cards type",
            ),
        ),
        migrations.AlterField(
            model_name="definition",
            name="language",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="definitions",
                to="languages.language",
                verbose_name="Язык",
            ),
        ),
        migrations.AlterField(
            model_name="definition",
            name="text",
            field=models.CharField(
                help_text="Определение слова или фразы",
                max_length=512,
                validators=[
                    django.core.validators.MinLengthValidator(2),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Digits Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. ",
                        regex="^([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Определение",
            ),
        ),
        migrations.AlterField(
            model_name="definition",
            name="translation",
            field=models.CharField(
                blank=True,
                max_length=512,
                validators=[
                    django.core.validators.MinLengthValidator(2),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure text begins with a letter.",
                        regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Перевод определения",
            ),
        ),
        migrations.AlterField(
            model_name="favoritecollection",
            name="collection",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="favorite_for",
                to="vocabulary.collection",
                verbose_name="Коллекция",
            ),
        ),
        migrations.AlterField(
            model_name="favoriteword",
            name="word",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="favorite_for",
                to="vocabulary.word",
                verbose_name="Слово",
            ),
        ),
        migrations.AlterField(
            model_name="formgroup",
            name="color",
            field=models.CharField(
                blank=True,
                max_length=7,
                validators=[
                    django.core.validators.MinLengthValidator(7),
                    apps.core.validators.CustomRegexValidator(
                        message="Color must be in hex format.", regex="^#[\\w]+$"
                    ),
                ],
                verbose_name="Цвет группы",
            ),
        ),
        migrations.AlterField(
            model_name="formgroup",
            name="language",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="form_groups",
                to="languages.language",
                verbose_name="Язык",
            ),
        ),
        migrations.AlterField(
            model_name="formgroup",
            name="name",
            field=models.CharField(
                max_length=64,
                validators=[
                    django.core.validators.MinLengthValidator(1),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Digits Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. ",
                        regex="^([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Название группы",
            ),
        ),
        migrations.AlterField(
            model_name="formgroup",
            name="translation",
            field=models.CharField(
                blank=True,
                max_length=64,
                validators=[
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure text begins with a letter.",
                        regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    )
                ],
                verbose_name="Перевод названия группы",
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
        migrations.AlterField(
            model_name="quoteassociation",
            name="quote_author",
            field=models.CharField(
                blank=True,
                max_length=64,
                validators=[
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure text begins with a letter.",
                        regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    )
                ],
                verbose_name="Автор Цитаты",
            ),
        ),
        migrations.AlterField(
            model_name="quoteassociation",
            name="text",
            field=models.CharField(
                max_length=256,
                validators=[
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure text begins with a letter.",
                        regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    )
                ],
                verbose_name="Текст цитаты",
            ),
        ),
        migrations.AlterField(
            model_name="synonym",
            name="note",
            field=models.CharField(
                blank=True,
                help_text="Заметка для %(class)ss",
                max_length=256,
                verbose_name="Заметка",
            ),
        ),
        migrations.AlterField(
            model_name="usageexample",
            name="language",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="examples",
                to="languages.language",
                verbose_name="Язык",
            ),
        ),
        migrations.AlterField(
            model_name="usageexample",
            name="source",
            field=models.CharField(
                choices=[
                    ("other", "Другое"),
                    ("book", "Книга"),
                    ("film", "Фильм"),
                    ("song", "Песня"),
                    ("quote", "Quote"),
                ],
                default="other",
                max_length=64,
                verbose_name="Источник примера",
            ),
        ),
        migrations.AlterField(
            model_name="usageexample",
            name="source_url",
            field=models.CharField(
                blank=True,
                max_length=512,
                null=True,
                verbose_name="Ссылка на источник примера",
            ),
        ),
        migrations.AlterField(
            model_name="usageexample",
            name="text",
            field=models.CharField(
                help_text="Пример использования слова или фразы",
                max_length=512,
                validators=[
                    django.core.validators.MinLengthValidator(2),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Digits Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. ",
                        regex="^([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Пример использования",
            ),
        ),
        migrations.AlterField(
            model_name="usageexample",
            name="translation",
            field=models.CharField(
                blank=True,
                max_length=512,
                validators=[
                    django.core.validators.MinLengthValidator(2),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure text begins with a letter.",
                        regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Перевод примера",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="activity_status",
            field=models.CharField(
                choices=[("I", "Inactive"), ("A", "Active"), ("M", "Mastered")],
                default="I",
                max_length=8,
                verbose_name="Статус активности",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="antonyms",
            field=models.ManyToManyField(
                blank=True,
                help_text="Слова с обратным значением",
                through="vocabulary.Antonym",
                to="vocabulary.word",
                verbose_name="Антонимы",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="definitions",
            field=models.ManyToManyField(
                blank=True,
                related_name="words",
                through="vocabulary.WordDefinitions",
                to="vocabulary.definition",
                verbose_name="Определения",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="examples",
            field=models.ManyToManyField(
                blank=True,
                related_name="words",
                through="vocabulary.WordUsageExamples",
                to="vocabulary.usageexample",
                verbose_name="Пример использования",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="form_groups",
            field=models.ManyToManyField(
                blank=True,
                related_name="words",
                through="vocabulary.WordsFormGroups",
                to="vocabulary.formgroup",
                verbose_name="Группа форм слова",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="forms",
            field=models.ManyToManyField(
                blank=True,
                help_text="Формы слов",
                through="vocabulary.Form",
                to="vocabulary.word",
                verbose_name="Формы",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="image_associations",
            field=models.ManyToManyField(
                blank=True,
                related_name="words",
                through="vocabulary.WordImageAssociations",
                to="vocabulary.imageassociation",
                verbose_name="Ассоциация-картинка",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="is_problematic",
            field=models.BooleanField(
                default=False, verbose_name="Проблемно ли для вас это слово"
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="language",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="words",
                to="languages.language",
                verbose_name="Язык",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="last_exercise_date",
            field=models.DateTimeField(
                editable=False, null=True, verbose_name="Дата последней тренировки"
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="note",
            field=models.CharField(
                blank=True, max_length=256, verbose_name="Текст заметки"
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="quote_associations",
            field=models.ManyToManyField(
                blank=True,
                related_name="words",
                through="vocabulary.WordQuoteAssociations",
                to="vocabulary.quoteassociation",
                verbose_name="Ассоциация-цитата",
            ),
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
        migrations.AlterField(
            model_name="word",
            name="synonyms",
            field=models.ManyToManyField(
                blank=True,
                help_text="Слова с похожим значением",
                through="vocabulary.Synonym",
                to="vocabulary.word",
                verbose_name="Синонимы",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="tags",
            field=models.ManyToManyField(
                blank=True,
                related_name="words",
                to="vocabulary.wordtag",
                verbose_name="Теги слова",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="text",
            field=models.CharField(
                max_length=256,
                validators=[
                    django.core.validators.MinLengthValidator(1),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure text begins with a letter.",
                        regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Слово или фраза",
            ),
        ),
        migrations.AlterField(
            model_name="word",
            name="translations",
            field=models.ManyToManyField(
                blank=True,
                related_name="words",
                through="vocabulary.WordTranslations",
                to="vocabulary.wordtranslation",
                verbose_name="Переводы",
            ),
        ),
        migrations.AlterField(
            model_name="worddefinitions",
            name="definition",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.definition",
                verbose_name="Определение",
            ),
        ),
        migrations.AlterField(
            model_name="worddefinitions",
            name="word",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.word",
                verbose_name="Слово",
            ),
        ),
        migrations.AlterField(
            model_name="wordimageassociations",
            name="image",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.imageassociation",
                verbose_name="Ассоциация-картинка",
            ),
        ),
        migrations.AlterField(
            model_name="wordimageassociations",
            name="word",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.word",
                verbose_name="Слово",
            ),
        ),
        migrations.AlterField(
            model_name="wordquoteassociations",
            name="quote",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.quoteassociation",
                verbose_name="Ассоциация-цитата",
            ),
        ),
        migrations.AlterField(
            model_name="wordquoteassociations",
            name="word",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.word",
                verbose_name="Слово",
            ),
        ),
        migrations.AlterField(
            model_name="wordsformgroups",
            name="forms_group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="%(class)s",
                to="vocabulary.formgroup",
                verbose_name="Группа форм",
            ),
        ),
        migrations.AlterField(
            model_name="wordsformgroups",
            name="word",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.word",
                verbose_name="Слово",
            ),
        ),
        migrations.AlterField(
            model_name="wordsincollections",
            name="collection",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.collection",
                verbose_name="Коллекция",
            ),
        ),
        migrations.AlterField(
            model_name="wordsincollections",
            name="word",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.word",
                verbose_name="Слово",
            ),
        ),
        migrations.AlterField(
            model_name="wordtag",
            name="name",
            field=models.CharField(
                max_length=32,
                validators=[
                    django.core.validators.MinLengthValidator(1),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure text begins with a letter.",
                        regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Имя тега",
            ),
        ),
        migrations.AlterField(
            model_name="wordtranslation",
            name="language",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="word_translations",
                to="languages.language",
                verbose_name="Язык",
            ),
        ),
        migrations.AlterField(
            model_name="wordtranslation",
            name="text",
            field=models.CharField(
                help_text="Перевод слова или фразы на другой язык",
                max_length=256,
                validators=[
                    django.core.validators.MinLengthValidator(1),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure text begins with a letter.",
                        regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Перевод",
            ),
        ),
        migrations.AlterField(
            model_name="wordtranslations",
            name="translation",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.wordtranslation",
                verbose_name="Перевод",
            ),
        ),
        migrations.AlterField(
            model_name="wordtranslations",
            name="word",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.word",
                verbose_name="Слово",
            ),
        ),
        migrations.AlterField(
            model_name="wordtype",
            name="name",
            field=models.CharField(
                max_length=64,
                unique=True,
                validators=[
                    django.core.validators.MinLengthValidator(1),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure text begins with a letter.",
                        regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Имя типа слова",
            ),
        ),
        migrations.AlterField(
            model_name="wordtype",
            name="name_en",
            field=models.CharField(
                max_length=64,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.MinLengthValidator(1),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure text begins with a letter.",
                        regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Имя типа слова",
            ),
        ),
        migrations.AlterField(
            model_name="wordtype",
            name="name_ru",
            field=models.CharField(
                max_length=64,
                null=True,
                unique=True,
                validators=[
                    django.core.validators.MinLengthValidator(1),
                    apps.core.validators.CustomRegexValidator(
                        message="Acceptable characters: Letters from any language, Hyphen, Exclamation point, Question mark, Dot, Comma, Colon, Apostrophe, Slash. Make sure text begins with a letter.",
                        regex="^(\\p{L}+)([\\p{L}-!?.,:/&'`’() \\d]*)$",
                    ),
                ],
                verbose_name="Имя типа слова",
            ),
        ),
        migrations.AlterField(
            model_name="wordusageexamples",
            name="example",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.usageexample",
                verbose_name="Пример использования",
            ),
        ),
        migrations.AlterField(
            model_name="wordusageexamples",
            name="word",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(class)s",
                to="vocabulary.word",
                verbose_name="Слово",
            ),
        ),
        migrations.AddConstraint(
            model_name="word",
            constraint=models.UniqueConstraint(
                models.F("text"),
                models.F("author"),
                models.F("language"),
                name="unique_words_in_user_voc",
            ),
        ),
    ]
