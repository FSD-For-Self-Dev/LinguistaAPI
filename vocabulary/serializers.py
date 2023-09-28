''' Vocabulary serializers '''

from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Definition, Tag, Translation, UsageExample, Word  # Synonym

User = get_user_model()


# class SynonymSerializer(serializers.ModelSerializer):
#     synonym = serializers.StringRelatedField()

#     class Meta:
#         model = Synonym
#         fields = (
#             'synonym', 'note'
#         )


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


class WordListSerializer(serializers.ModelSerializer):
    translations_count = serializers.IntegerField()
    translations = TranslationSerializer(many=True)
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='name', many=True
    )
    author = serializers.SlugRelatedField(
        slug_field='username', many=False, read_only=True
    )

    class Meta:
        model = Word
        fields = (
            'id', 'language', 'text', 'activity', 'type', 'note', 'tags',
            'translations_count', 'translations', 'created', 'author'
        )
        read_only_fields = fields


class WordSerializer(serializers.ModelSerializer):
    translations_count = serializers.IntegerField()
    examples_count = serializers.IntegerField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    translations = TranslationSerializer(many=True)
    examples = UsageExampleSerializer(many=True)
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='name', many=True
    )
    # synonyms = SynonymSerializer(many=True)
    # synonyms = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = (
            'id', 'language', 'text', 'activity', 'is_problematic', 'type', 'note', 'tags',
            'translations_count', 'translations', 'examples_count',
            'examples', 'created', 'author'
        )
        read_only_fields = ('id',)

    # def get_synonyms(self, obj):
    #     return SynonymSerializer(
    #         obj.synonyms.all() | obj.being_synonym_to.all(),
    #         many=True,
    #         context={'request': self.context.get('request')}
    #     ).data

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


class WordShortResponseSerializer(serializers.ModelSerializer):
    translations_count = serializers.SerializerMethodField()
    examples_count = serializers.SerializerMethodField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='name', many=True
    )

    def get_translations_count(self, obj):
        return obj.translations.count()

    def get_examples_count(self, obj):
        return obj.wordusageexamples.count()

    class Meta:
        model = Word
        fields = (
            'id', 'language', 'text', 'activity', 'is_problematic', 'type', 'tags',
            'translations_count', 'examples_count',
            'created', 'modified', 'author'
        )
        read_only_fields = ('id',)


class DefinitionSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Definition
        fields = ('id', 'author', 'text', 'translation', 'created', 'modified')
        read_only_fields = ('id', 'author', 'created', 'modified')
