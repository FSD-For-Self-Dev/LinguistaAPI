from django.contrib.auth import get_user_model

from rest_framework import serializers

from words.models import Word

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

    class Meta:
        model = Word
        fields = (
            'id', 'text', 'language', 'status', 'type',
            'note', 'translations_count'
        )

    def get_translations_count(self, obj):
        return obj.translations.count()

