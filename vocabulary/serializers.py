"""Vocabulary serializers."""

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import (
    Definition, FavoriteWord, Note, Tag,
    Translation, UsageExample, Word, WordDefinitions, WordTranslations,
    WordUsageExamples, Synonym, Antonym, Form, Similar
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
        write_only_fields = ('author',)


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

    # def to_representation(self, instance):
    #     ret = {'text': instance.text}
    #     return ret

    class Meta:
        model = Word
        fields = ('text', 'author')


class WordSerializer(serializers.ModelSerializer):
    """Сериализатор для множественного добавления слов (а также синонимов,
    антонимов, форм и похожих слов)."""
    translations = TranslationSerializer(many=True)
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    favorite = serializers.SerializerMethodField()
    notes = NoteSerializer(source='note', many=True, required=False)

    class Meta:
        model = Word
        fields = (
            'text', 'translations', 'author', 'favorite', 'collections',
            'notes'
        )

    def get_favorite(self, obj):
        request = self.context.get('request')
        is_favorite = FavoriteWord.objects.filter(
            word=obj, user=request.user
        ).exists()
        return is_favorite

    def get_notes(self, obj):
        return obj.notes.all()

    def validate(self, data):
        request = self.context['request']
        author_id = request.user
        text = data.get('text')
        if Word.objects.filter(author=author_id, text=text).exists():
            raise serializers.ValidationError(
                'The word is already in the dictionary'
            )

        if len(data['translations']) == 0:
            raise serializers.ValidationError(
                'The word must have at least one translation'
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        translations = validated_data.pop('translations')
        collections = validated_data.pop('collections', [])
        notes = validated_data.pop('notes', [])

        word = Word.objects.create(**validated_data)

        word.collections.set(collections)

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


class AdvancedWordSerializer(WordSerializer):
    """Расширенный (полный) сериализатор для создания слов по одному."""
    language = serializers.StringRelatedField()
    translations_count = serializers.SerializerMethodField()
    examples = UsageExampleSerializer(many=True, required=False)
    examples_count = serializers.SerializerMethodField()
    definitions = DefinitionSerializer(many=True, required=False)
    type = serializers.StringRelatedField()
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='name', many=True,
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
            'is_problematic', 'activity', 'collections', 'created', 'synonyms',
            'favorite', 'author', 'antonyms', 'forms', 'similars'
        )
        read_only_fields = ('id',)

    def get_translations_count(self, obj):
        return obj.translations.count()

    def get_examples_count(self, obj):
        return obj.wordusageexamples.count()

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        examples = validated_data.pop('examples', [])
        definitions = validated_data.pop('definitions', [])
        synonyms = validated_data.pop('synonyms', [])
        antonyms = validated_data.pop('antonyms', [])
        forms = validated_data.pop('forms', [])
        similars = validated_data.pop('similars', [])

        word = super().create(validated_data)
        word.tags.set(tags)

        example_objs = [UsageExample(**data) for data in examples]
        UsageExample.objects.bulk_create(example_objs)
        WordUsageExamples.objects.bulk_create(
            [
                WordUsageExamples(
                    word=word,
                    example=example
                ) for example in example_objs
            ]
        )

        definition_objs = [Definition(**data) for data in definitions]
        Definition.objects.bulk_create(definition_objs)
        WordDefinitions.objects.bulk_create(
            [
                WordDefinitions(
                    word=word,
                    definition=definition
                ) for definition in definition_objs
            ]
        )

        for synonym in synonyms:
            synonym_word = Word.objects.get(
                text=synonym.get('text'),
                author=self.context['request'].user
            )
            Synonym.objects.create(
                to_word=word,
                from_word=synonym_word,
                author=self.context['request'].user
            )

        for antonym in antonyms:
            antonym_word = Word.objects.get(
                text=antonym.get('text'),
                author=self.context['request'].user
            )
            Antonym.objects.create(
                to_word=word,
                from_word=antonym_word,
                author=self.context['request'].user
            )

        for form in forms:
            form_word = Word.objects.get(
                text=form.get('text'),
                author=self.context['request'].user
            )
            Form.objects.create(
                to_word=word,
                from_word=form_word,
                author=self.context['request'].user
            )

        for similar in similars:
            similar_word = Word.objects.get(
                text=similar.get('text'),
                author=self.context['request'].user
            )
            Similar.objects.create(
                to_word=word,
                from_word=similar_word,
                author=self.context['request'].user
            )

        return word
