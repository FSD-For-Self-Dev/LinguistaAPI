"""Сериализаторы приложения vocabulary."""

from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import Tag, Translation, UsageExample, Word  # Synonym

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
        fields = ('translation',  'definition', 'definition_translation')


class ExampleSerializer(serializers.ModelSerializer):

    class Meta:
        model = UsageExample
        fields = ('example',  'translation')


class VocabularySerializer(serializers.ModelSerializer):
    translations_count = serializers.SerializerMethodField()
    examples_count = serializers.SerializerMethodField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    translations  = TranslationSerializer(many=True)
    examples  = ExampleSerializer(many=True)
    tags = serializers.SlugRelatedField(
        queryset=Tag.objects.all(), slug_field='name', many=True
    )
    # synonyms = SynonymSerializer(many=True)
    # synonyms = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = (
            'id', 'language', 'text', 'status', 'type', 'note', 'tags',
            'translations_count', 'translations', 'examples_count',
            'examples', 'created', 'author'
        )
        read_only_fields = ('id',)

    def get_translations_count(self, obj):
        return obj.translations.count()

    def get_examples_count(self, obj):
        return obj.examples.count()

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
