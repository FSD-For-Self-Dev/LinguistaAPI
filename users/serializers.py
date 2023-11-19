''' Users serializers '''

from django.contrib.auth import get_user_model

from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор модели пользователя."""

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'image',
        )
        read_only_fields = ('id',)
