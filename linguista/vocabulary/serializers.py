''' Vocabulary serializers '''

from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Tag, Translation, UsageExample, Word, Definition, Word  # Synonym

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

    class Meta:
        model = UsageExample
        fields = ('text',  'translation')


class WordSerializer(serializers.ModelSerializer):
    translations_count = serializers.SerializerMethodField()
    examples_count = serializers.SerializerMethodField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    translations = TranslationSerializer(many=True)
    wordusageexamples = UsageExampleSerializer(many=True)
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='name', many=True
    )
    # synonyms = SynonymSerializer(many=True)
    # synonyms = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = (
            'id', 'language', 'text', 'activity', 'type', 'note', 'tags',
            'translations_count', 'translations', 'examples_count',
            'wordusageexamples', 'created', 'author'
        )
        read_only_fields = ('id',)

    def get_translations_count(self, obj):
        return obj.translations.count()

    def get_examples_count(self, obj):
        return obj.wordusageexamples.count()

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


class DefinitionSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Definition
        fields = ('id', 'author', 'text', 'translation', 'created', 'modified')
        read_only_fields = ('id', 'author', 'created', 'modified')


class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = '__all__'
