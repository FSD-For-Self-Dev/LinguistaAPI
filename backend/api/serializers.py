from django.contrib.auth import get_user_model

from rest_framework import serializers

from words.models import Word, Translation

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    ...
#     is_subscribed = serializers.SerializerMethodField()

#     class Meta:
#         model = User
#         fields = (
#             'id', 'username', 'email', 'first_name', 'last_name',
#             'is_subscribed'
#         )

#     def get_is_subscribed(self, obj):
#         user = self.context['request'].user
#         return (
#             user.is_authenticated
#             and Follow.objects.filter(user=user, following=obj).exists()
#         )


class WordSerializer(serializers.ModelSerializer):
    translations_count = serializers.SerializerMethodField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Word
        fields = (
            'id', 'text', 'language', 'status', 'type',
            'note', 'translations_count', 'translations', 'author'
        )
        read_only_fields = ('id',)

    def get_translations_count(self, obj):
        return obj.translations.count()

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


class TranslationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Translation
        fields = '__all__'
