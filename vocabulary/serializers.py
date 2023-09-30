''' Vocabulary serializers '''

from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Tag, Translation, UsageExample, Word, Definition, Collection  # Synonym

User = get_user_model()


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
    translations_count = serializers.IntegerField()
    examples_count = serializers.IntegerField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    translations = TranslationSerializer(many=True)
    examples = UsageExampleSerializer(many=True)
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='name', many=True
    )

    class Meta:
        model = Word
        fields = (
            'id', 'language', 'text', 'activity', 'type', 'note', 'tags',
            'translations_count', 'translations', 'examples_count',
            'examples', 'created', 'author'
        )
        read_only_fields = ('id',)

    def create(self, validated_data):
        translations = validated_data.pop('translations')
        tags = validated_data.pop('tags', [])
        collections = validated_data.pop('collections', [])

        word = Word.objects.create(**validated_data)
        word.tags.set(tags)
        word.collections.set(collections)

        translations_objs = [Translation(
            word=word,
            **data
        ) for data in translations]
        Translation.objects.bulk_create(translations_objs)

        return word


class DefinitionSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Definition
        fields = ('id', 'author', 'text', 'translation', 'created', 'modified')
        read_only_fields = ('id', 'author', 'created', 'modified')


class CollectionSerializer(serializers.ModelSerializer):
    """Сериалайзер коллекций"""
    words = serializers.SlugRelatedField(
        queryset=Word.objects.all(), slug_field='text', many=True
    )

    class Meta:
        model = Collection
        fields = ('title', 'words', 'description')
