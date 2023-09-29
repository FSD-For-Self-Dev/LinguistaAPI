"""Vocabulary serializers."""

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import (
    Antonym, Collection, Definition, FavoriteWord, Form, Note, Similar,
    Synonym, Tag, Translation, UsageExample, Word, WordDefinitions,
    WordTranslations, WordUsageExamples
)

User = get_user_model()


class NoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Note
        fields = ('text',)


class TranslationSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Translation
        fields = ('text', 'author')


class UsageExampleSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = UsageExample
        fields = ('id', 'author', 'text', 'translation', 'created', 'modified')
        read_only_fields = ('id', 'author', 'created', 'modified')


class DefinitionSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Definition
        fields = ('id', 'author', 'text', 'translation', 'created', 'modified')
        read_only_fields = ('id', 'author', 'created', 'modified')


class WordRelatedSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Word
        fields = ('id', 'text', 'author')


class WordShortSerializer(serializers.ModelSerializer):
    """Сериализатор для множественного добавления слов (а также синонимов,
    антонимов, форм и похожих слов), а также для чтения в короткой форме."""
    language = serializers.StringRelatedField()
    type = serializers.StringRelatedField()
    notes = NoteSerializer(
        source='note', many=True, required=False, write_only=True
    )
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='name', many=True,
        required=False
    )
    translations_count = serializers.IntegerField(read_only=True)
    translations = TranslationSerializer(many=True)
    favorite = serializers.SerializerMethodField()
    collections = serializers.SlugRelatedField(
        queryset=Collection.objects.all(), slug_field='title', many=True,
        required=False, write_only=True
    )
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Word
        fields = (
            'id', 'language', 'text', 'activity', 'is_problematic', 'type',
            'notes', 'tags', 'translations_count', 'translations', 'favorite',
            'collections', 'created', 'modified', 'author'
        )
        read_only_fields = (
            'id', 'is_problematic', 'translations_count'
        )

    def get_favorite(self, obj):
        request = self.context.get('request')
        is_favorite = FavoriteWord.objects.filter(
            word=obj, user=request.user
        ).exists()
        return is_favorite

    def validate(self, data):
        # request = self.context['request']
        # author_id = request.user
        # text = data.get('text')
        # if Word.objects.filter(author=author_id, text=text).exists():
        #     raise serializers.ValidationError(
        #         'The word is already in the dictionary'
        #     )

        translations = data.get('translations')
        if not translations or len(translations) == 0:
            raise serializers.ValidationError(
                'The word must have at least one translation'
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        translations = validated_data.pop('translations')
        collections = validated_data.pop('collections', [])
        notes = validated_data.pop('notes', [])
        tags = validated_data.pop('tags', [])

        word = Word.objects.create(**validated_data)

        word.collections.set(collections)
        word.tags.set(tags)

        for translation in translations:
            current_translation, created = (
                Translation.objects.get_or_create(**translation)
            )
            WordTranslations.objects.create(
                word=word, translation=current_translation
            )

        note_objs = [Note(word=word, **data) for data in notes]
        Note.objects.bulk_create(note_objs)

        return word


class WordSerializer(WordShortSerializer):
    """Расширенный (полный) сериализатор для создания слов по одному."""
    examples = UsageExampleSerializer(many=True, required=False)
    examples_count = serializers.IntegerField(read_only=True)
    definitions = DefinitionSerializer(many=True, required=False)
    notes = NoteSerializer(source='note', many=True, required=False)
    collections = serializers.SlugRelatedField(
        queryset=Collection.objects.all(), slug_field='title', many=True,
        required=False
    )

    synonyms = WordRelatedSerializer(many=True, required=False)
    antonyms = WordRelatedSerializer(many=True, required=False)
    forms = WordRelatedSerializer(many=True, required=False)
    similars = WordRelatedSerializer(many=True, required=False)

    class Meta:
        model = Word
        fields = (
            'id', 'language', 'text', 'translations', 'translations_count',
            'examples_count', 'examples', 'definitions', 'type', 'tags',
            'is_problematic', 'activity', 'collections', 'created', 'modified',
            'synonyms', 'favorite', 'author', 'antonyms', 'forms', 'similars',
            'notes'
        )
        read_only_fields = ('id', 'translations_count', 'examples_count')

    @staticmethod
    def bulk_create_objects(
            objs, model_cls, related_model_cls, related_field, word
    ):
        objs_list = [model_cls(**data) for data in objs]
        model_cls.objects.bulk_create(objs_list)
        related_objs_list = [
            related_model_cls(
                **{
                    related_field: related_data,
                    'word': word
                }
            ) for related_data in objs_list
        ]
        related_model_cls.objects.bulk_create(related_objs_list)

    def create_links_for_related_objs(self, cls, objs, word):
        for obj in objs:
            obj_word = Word.objects.get(
                text=obj.get('text'),
                author=self.context['request'].user
            )
            cls.objects.create(
                to_word=word,
                from_word=obj_word,
                author=self.context['request'].user
            )

    @transaction.atomic
    def create(self, validated_data):
        examples = validated_data.pop('examples', [])
        definitions = validated_data.pop('definitions', [])
        synonyms = validated_data.pop('synonyms', [])
        antonyms = validated_data.pop('antonyms', [])
        forms = validated_data.pop('forms', [])
        similars = validated_data.pop('similars', [])

        word = super().create(validated_data)

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
