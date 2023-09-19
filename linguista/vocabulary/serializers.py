"""Vocabulary serializers."""

from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Definition,
    Note,
    Tag,
    Translation,
    UsageExample,
    Word,
    WordUsageExamples,
)
# Synonym

User = get_user_model()


# class SynonymSerializer(serializers.ModelSerializer):
#     synonym = serializers.StringRelatedField()

#     class Meta:
#         model = Synonym
#         fields = (
#             'synonym', 'note'
#         )

class NoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Note
        fields = ('text',)


class TranslationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Translation
        fields = ('text',)


class UsageExampleSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = UsageExample
        fields = ('id', 'author', 'text', 'translation', 'created', 'modified')
        read_only_fields = ('id', 'author', 'created', 'modified')


class WordSerializer(serializers.ModelSerializer):
    translations_count = serializers.SerializerMethodField()
    examples_count = serializers.SerializerMethodField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    translations = TranslationSerializer(many=True)
    wordusageexamples = UsageExampleSerializer(many=True, default=[])
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='name', many=True, default=[]
    )
    notes = NoteSerializer(many=True, default=[])
    # synonyms = SynonymSerializer(many=True)
    # synonyms = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = (
            'id', 'language', 'text', 'activity', 'type', 'notes', 'tags',
            'translations_count', 'translations', 'examples_count',
            'wordusageexamples', 'created', 'author'
        )
        read_only_fields = ('id',)

    def get_translations_count(self, obj):
        return obj.translations.count()

    def get_examples_count(self, obj):
        return obj.wordusageexamples.count()

    def validate(self, data):
        if len(data['translations']) == 0:
            raise serializers.ValidationError(
                'У слова должен быть хотя бы один перевод'
            )

    # def get_synonyms(self, obj):
    #     return SynonymSerializer(
    #         obj.synonyms.all() | obj.being_synonym_to.all(),
    #         many=True,
    #         context={'request': self.context.get('request')}
    #     ).data

    @transaction.atomic
    def create(self, validated_data):
        translations = validated_data.pop('translations')
        tags = validated_data.pop('tags', [])
        collections = validated_data.pop('collections', [])
        wordusageexamples = validated_data.pop('wordusageexamples', [])
        notes = validated_data.pop('notes', [])

        word = Word.objects.create(**validated_data)
        word.tags.set(tags)
        word.collections.set(collections)

        translations_objs = [Translation(
            word=word,
            **data
        ) for data in translations]
        Translation.objects.bulk_create(translations_objs)
        wordusageexamples_objs = [WordUsageExamples(
            word=word,
            **data,
        ) for data in wordusageexamples]
        WordUsageExamples.objects.bulk_create(wordusageexamples_objs)
        notes_objs = [Note(
            word=word,
            **data,
        ) for data in notes]
        Note.objects.bulk_create(notes_objs)

        return word

    # @staticmethod
    # def set_additional_fields(Model, word, data):
    #     objs = [Model(
    #         word=word,
    #         **item,
    #     ) for item in data]
    #     Model.objects.bulk_create(objs)


class DefinitionSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Definition
        fields = ('id', 'author', 'text', 'translation', 'created', 'modified')
        read_only_fields = ('id', 'author', 'created', 'modified')
