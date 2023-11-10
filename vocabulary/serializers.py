"""Сериализаторы приложения vocabulary."""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.translation import gettext as _

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from users.serializers import UserSerializer

from .constants import (
    MAX_ANTONYMS_AMOUNT, MAX_DEFINITIONS_AMOUNT, MAX_EXAMPLES_AMOUNT,
    MAX_FORMS_AMOUNT, MAX_NOTES_AMOUNT, MAX_SIMILARS_AMOUNT,
    MAX_SYNONYMS_AMOUNT, MAX_TAGS_AMOUNT, MAX_TRANSLATIONS_AMOUNT,
    MAX_TYPES_AMOUNT,
)
from .models import (
    Antonym, Collection, Definition, FavoriteWord, Form, FormsGroup, Language,
    Note, Similar, Synonym, Tag, WordTranslation, Type, UsageExample, Word,
    WordDefinitions, WordTranslations, WordUsageExamples,
)

User = get_user_model()


class ReadWriteSerializerMethodField(serializers.SerializerMethodField):
    """Поле для чтения и записи полей вне модели."""

    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs['source'] = '*'
        super(serializers.SerializerMethodField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        return {self.field_name: data}

    def to_representation(self, value):
        method = getattr(self.parent, self.method_name)
        return method(value)


class RelatedSerializerField(serializers.PrimaryKeyRelatedField):
    """
    Кастомное поле для использования в сериализаторе слов.

    Позволяет при записи передавать id объектов,
    а при чтении выводить данные сериализатора.
    """

    def __init__(self, serializer_class, many=False, **kwargs):
        self.serializer_class = serializer_class
        self.many = many
        super().__init__(**kwargs)

    def to_representation(self, value):
        return self.serializer_class(
            value, many=self.many, required=self.required
        ).data


class CreatableSlugRelatedField(serializers.SlugRelatedField):
    """
    Поле для получения объекта по слагу или создания объекта с таким слагом, 
    если его нет.
    """

    def to_internal_value(self, data):
        try:
            obj, created = self.get_queryset().get_or_create(
                **{self.slug_field: data}
            )
            return obj
        except (TypeError, ValueError):
            self.fail('invalid')


class AddAuthorInCreateSerializer(serializers.ModelSerializer):
    """Абстрактная модель для добавления автора в методе create."""

    class Meta:
        abstract=True

    def create(self, validated_data):
        return self.Meta.model.objects.create(
            author=self.context['request'].user,
            **validated_data
        )


class WordSameLanguageDefault:
    requires_context = True

    def __call__(self, serializer_field):
        request_data = serializer_field.context['request'].data
        try:
            return Language.objects.get(name=request_data['language'])
        except KeyError:
            return None

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class NoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Note
        fields = ('text', 'created')
        read_only_fields = ('created',)


class TranslationSerializer(AddAuthorInCreateSerializer):
    author = serializers.SlugRelatedField(
        many=False, slug_field='username', read_only=True
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(), slug_field='name',
        default=WordSameLanguageDefault()
        # нужно будет исправить default на родной язык пользователя
    )

    class Meta:
        model = WordTranslation
        fields = ('id', 'text', 'language', 'author')
        read_only_fields = ('id', 'author')


class UsageExampleSerializer(AddAuthorInCreateSerializer):
    author = serializers.SlugRelatedField(
        many=False, slug_field='username', read_only=True
    )

    class Meta:
        model = UsageExample
        fields = ('id', 'author', 'text', 'translation', 'created', 'modified')
        read_only_fields = ('id', 'author', 'created', 'modified')


class DefinitionSerializer(AddAuthorInCreateSerializer):
    author = serializers.SlugRelatedField(
        many=False, slug_field='username', read_only=True
    )

    class Meta:
        model = Definition
        fields = ('id', 'author', 'text', 'translation', 'created', 'modified')
        read_only_fields = ('id', 'author', 'created', 'modified')


class CollectionShortSerializer(AddAuthorInCreateSerializer):
    author = serializers.SlugRelatedField(
        many=False, slug_field='username', read_only=True
    )
    words_count = serializers.SerializerMethodField()
    last_3_words = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = (
            'id', 'slug', 'author', 'title', 'words_count', 'last_3_words',
            'created', 'modified'
        )
        read_only_fields = (
            'id', 'slug', 'words_count', 'created', 'modified'
        )

    def get_words_count(self, obj):
        return obj.words.count()

    def get_last_3_words(self, obj):
        return obj.words.order_by('-wordsincollections__created').values_list(
            'text', flat=True
        )[:3]


class FormsGroupSerializer(AddAuthorInCreateSerializer):
    author = serializers.SlugRelatedField(
        many=False, slug_field='username', read_only=True
    )

    class Meta:
        model = FormsGroup
        fields = ('id', 'slug', 'name', 'author')
        read_only_fields = ('id', 'slug', 'author')

    def validate_name(self, name):
        if name.capitalize() == 'Infinitive':
            raise serializers.ValidationError(
                'The forms group `Infinitive` already exists.'
            )
        return name


class WordRelatedSerializer(AddAuthorInCreateSerializer):
    """Сериализатор для короткой демонстрации word-related объектов
    (синонимы, антонимы, похожие слова и формы)."""

    author = serializers.SlugRelatedField(
        many=False, slug_field='username', read_only=True
    )
    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(), slug_field='name',
        default=WordSameLanguageDefault()
    )

    class Meta:
        model = Word
        fields = ('id', 'language', 'text', 'author')


class WordShortSerializer(serializers.ModelSerializer):
    """Сериализатор для множественного добавления слов (а также синонимов,
    антонимов, форм и похожих слов), а также для чтения в короткой форме."""

    language = serializers.SlugRelatedField(
        queryset=Language.objects.all(), slug_field='name', required=True
    )
    types = serializers.SlugRelatedField(
        slug_field='name', queryset=Type.objects.all(), many=True,
        required=False
    )
    tags = CreatableSlugRelatedField(
        slug_field='name', queryset=Tag.objects.all(), many=True,
        required=False
    )
    notes = NoteSerializer(many=True, required=False)
    translations_count = serializers.IntegerField(read_only=True)
    translations = TranslationSerializer(many=True, required=False)
    favorite = ReadWriteSerializerMethodField(
        method_name='get_favorite',
        required=False
    )
    author = UserSerializer(many=False, read_only=True)

    class Meta:
        model = Word
        fields = (
            'id', 'slug','language', 'text', 'activity', 'is_problematic',
            'types', 'notes', 'tags', 'translations_count', 'translations',
            'favorite', 'created', 'modified', 'author'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'is_problematic', 'translations_count'
        )

    @staticmethod
    def max_amount_validate(obj_list, max_amount, attr):
        """Статический метод для валидации максимального количества элементов
        произвольного атрибута слова."""
        if len(obj_list) > max_amount:
            raise serializers.ValidationError(
                f'The word cannot have more than '
                f'{max_amount} {attr}'
            )

    def validate_types(self, types):
        self.max_amount_validate(types, MAX_TYPES_AMOUNT, 'types')
        return types

    def validate_translations(self, translations):
        self.max_amount_validate(
            translations, MAX_TRANSLATIONS_AMOUNT, 'translations'
        )
        return translations

    def validate_tags(self, tags):
        self.max_amount_validate(tags, MAX_TAGS_AMOUNT, 'tags')
        return tags

    def validate_notes(self, notes):
        self.max_amount_validate(notes, MAX_NOTES_AMOUNT, 'notes')
        return notes

    @extend_schema_field(serializers.BooleanField)
    def get_favorite(self, obj):  # метод повторяется
        user = self.context['request'].user
        return FavoriteWord.objects.filter(word=obj, user=user).exists()

    @transaction.atomic
    def create(self, validated_data):
        translations = validated_data.pop('translations', [])
        word_types = validated_data.pop('types', [])
        notes = validated_data.pop('notes', [])
        tags = validated_data.pop('tags', [])
        favorite = validated_data.pop('favorite', None)

        context_user = self.context['request'].user

        word = Word.objects.create(author=context_user, **validated_data)

        if favorite:
            FavoriteWord.objects.create(user=context_user, word=word)

        word.tags.set(tags)
        word.types.set(word_types)

        for translation in translations:
            current_translation, created = (
                WordTranslation.objects.get_or_create(**translation)
            )
            WordTranslations.objects.create(
                word=word, translation=current_translation
            )

        note_objs = [Note(word=word, **data) for data in notes]
        Note.objects.bulk_create(note_objs)

        return word


class WordSerializer(WordShortSerializer):
    """Расширенный (полный) сериализатор для создания слов по одному,
    а также для просмотра слов."""

    collections = RelatedSerializerField(
        queryset=Collection.objects.all(), many=True, required=False,
        serializer_class=CollectionShortSerializer
    )
    collections_count = serializers.IntegerField(read_only=True)
    examples = UsageExampleSerializer(many=True, required=False)
    examples_count = serializers.IntegerField(read_only=True)
    definitions = DefinitionSerializer(many=True, required=False)
    synonyms = WordRelatedSerializer(many=True, required=False)
    antonyms = WordRelatedSerializer(many=True, required=False)
    forms = WordRelatedSerializer(many=True, required=False)
    similars = WordRelatedSerializer(many=True, required=False)

    class Meta:
        model = Word
        fields = (
            'id', 'slug', 'language', 'text', 'translations',
            'translations_count', 'examples_count', 'examples', 'definitions',
            'types', 'tags', 'is_problematic', 'activity', 'collections',
            'created', 'modified', 'synonyms', 'favorite', 'author',
            'antonyms', 'forms', 'similars', 'collections_count',
            'collections', 'notes'
        )
        read_only_fields = (
            'id', 'slug', 'translations_count', 'examples_count'
        )

    def validate_examples(self, examples):
        self.max_amount_validate(examples, MAX_EXAMPLES_AMOUNT, 'examples')
        return examples

    def validate_definitions(self, definitions):
        self.max_amount_validate(
            definitions, MAX_DEFINITIONS_AMOUNT, 'definitions'
        )
        return definitions

    def validate_synonyms(self, synonyms):
        self.max_amount_validate(synonyms, MAX_SYNONYMS_AMOUNT, 'synonyms')
        return synonyms

    def validate_antonyms(self, antonyms):
        self.max_amount_validate(antonyms, MAX_ANTONYMS_AMOUNT, 'antonyms')
        return antonyms

    def validate_similars(self, similars):
        self.max_amount_validate(similars, MAX_SIMILARS_AMOUNT, 'similars')
        return similars

    def validate_forms(self, forms):
        self.max_amount_validate(forms, MAX_FORMS_AMOUNT, 'forms')
        return forms

    @staticmethod
    def bulk_create_objects(
            objs, model_cls, related_model_cls, related_field, word
    ):
        """Статический метод для массового создания объектов
        для полей many-to-many."""
        objs_list = [model_cls(**data) for data in objs]
        model_cls.objects.bulk_create(objs_list)
        related_objs_list = [
            related_model_cls(
                **{
                    'word': word,
                    related_field: obj
                }
            ) for obj in objs_list
        ]
        related_model_cls.objects.bulk_create(related_objs_list)

    def create_links_for_related_objs(self, cls, objs, word):
        """Метод для создания связей между симметричными объектами слов."""
        for obj in objs:
            obj_word, created = Word.objects.get_or_create(
                author=self.context['request'].user,
                **obj
            )
            cls.objects.create(
                to_word=word,
                from_word=obj_word,
                author=self.context['request'].user
            )
            cls.objects.create(
                to_word=obj_word,
                from_word=word,
                author=self.context['request'].user
            )

    @transaction.atomic
    def create(self, validated_data):
        collections = validated_data.pop('collections', [])
        examples = validated_data.pop('examples', [])
        definitions = validated_data.pop('definitions', [])
        synonyms = validated_data.pop('synonyms', [])
        antonyms = validated_data.pop('antonyms', [])
        forms = validated_data.pop('forms', [])
        similars = validated_data.pop('similars', [])

        word = super().create(validated_data)
        word.collections.set(collections)

        self.bulk_create_objects(
            examples,
            UsageExample,
            WordUsageExamples,
            'example',
            word
        )
        self.bulk_create_objects(
            definitions,
            Definition,
            WordDefinitions,
            'definition',
            word
        )

        self.create_links_for_related_objs(Synonym, synonyms, word)
        self.create_links_for_related_objs(Antonym, antonyms, word)
        self.create_links_for_related_objs(Form, forms, word)
        self.create_links_for_related_objs(Similar, similars, word)

        return word


class TypeSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра всех возможных типов слов и фраз."""

    class Meta:
        model = Type
        fields = (
            'id',
            'name',
            'slug',
            'sorting',
        )
        read_only_fields = fields


class CollectionSerializer(AddAuthorInCreateSerializer):
    author = UserSerializer(many=False, read_only=True)
    words = WordShortSerializer(many=True, required=False)

    class Meta:
        model = Collection
        fields = (
            'id', 'slug', 'author', 'title', 'description', 'created',
            'modified', 'words'
        )
        read_only_fields = ('id', 'slug', 'author', 'created', 'modified')
