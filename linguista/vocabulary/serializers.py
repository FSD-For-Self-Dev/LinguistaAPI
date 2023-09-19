"""Vocabulary serializers."""

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import (
    Definition, FavoriteWord, Note, Tag,
    Translation, UsageExample, Word, WordDefinitions, WordTranslations,
    WordUsageExamples
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


# class WordShortSerializer(serializers.ModelSerializer):
#     """Сериализатор для быстрого добавления слов
#     (в том числе синонимов, антонимов, форм и похожих слов)."""
#     translations = TranslationSerializer(many=True)
#     author = serializers.HiddenField(default=serializers.CurrentUserDefault())
#
#     class Meta:
#         model = Word
#         fields = ('text', 'translations', 'author')
#
#     def validate(self, data):
#         if len(data['translations']) == 0:
#             raise serializers.ValidationError(
#                 'The word must have at least one translation'
#             )
#         return data


class WordSerializer(serializers.ModelSerializer):
    language = serializers.StringRelatedField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    translations = TranslationSerializer(many=True)
    translations_count = serializers.SerializerMethodField()
    examples = UsageExampleSerializer(many=True, default=[])
    examples_count = serializers.SerializerMethodField()
    definitions = DefinitionSerializer(many=True, default=[])
    type = serializers.StringRelatedField()
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='name', many=True, default=[]
    )
    favorite = serializers.SerializerMethodField()
    # collections = ...
    notes = NoteSerializer(many=True, default=[])
    # synonyms = WordShortSerializer(many=True, default=[])
    # antonyms = WordShortSerializer(many=True, default=[])
    # similars = WordShortSerializer(many=True, default=[])
    # forms = WordShortSerializer(many=True, default=[])
    # synonyms = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = (
            'id', 'language', 'text', 'author', 'translations',
            'translations_count', 'examples', 'examples_count', 'definitions',
            'type', 'tags', 'is_problematic', 'favorite', 'activity',
            'collections', 'notes', 'created'
            # 'synonyms', 'antonyms', 'similars', 'forms'
        )
        read_only_fields = ('id', 'activity')
        # read_only_fields = ('id',)

    def get_translations_count(self, obj):
        return obj.translations.count()

    def get_examples_count(self, obj):
        return obj.wordusageexamples.count()

    def get_favorite(self, obj):
        request = self.context.get('request')
        is_favorite = FavoriteWord.objects.filter(
            word=obj, user=request.user
        ).exists()
        return is_favorite

    def validate(self, data):
        if len(data['translations']) == 0:
            raise serializers.ValidationError(
                'The word must have at least one translation'
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        translations = validated_data.pop('translations')
        tags = validated_data.pop('tags', [])
        collections = validated_data.pop('collections', [])
        examples = validated_data.pop('examples', [])
        definitions = validated_data.pop('definitions', [])
        notes = validated_data.pop('notes', [])
        # synonyms = validated_data.pop('synonyms', [])
        # antonyms = validated_data.pop('antonyms', [])
        # similars = validated_data.pop('similars', [])
        # forms = validated_data.pop('forms', [])

        word = Word.objects.create(**validated_data)
        word.tags.set(tags)
        word.collections.set(collections)

        translation_objs = [Translation(**data) for data in translations]
        Translation.objects.bulk_create(translation_objs)
        WordTranslations.objects.bulk_create(
            [
                WordTranslations(
                    word=word,
                    translation=translation
                ) for translation in translation_objs
            ]
        )

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

        note_objs = [Note(word=word, **data) for data in notes]
        Note.objects.bulk_create(note_objs)

        return word

    # @staticmethod
    # def set_additional_fields(Model, word, data):
    #     objs = [Model(
    #         word=word,
    #         **item,
    #     ) for item in data]
    #     Model.objects.bulk_create(objs)
